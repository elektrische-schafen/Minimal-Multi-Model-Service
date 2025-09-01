import google.generativeai as genai
import os, json, requests, threading, logging
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
from groq import Groq
from PIL import Image
from io import BytesIO
from google.cloud import vision
import re
import time
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

client_groq = Groq(api_key=os.getenv("GROQ_API"))

client = vision.ImageAnnotatorClient.from_service_account_file(
    "Documents/vision_api_keys_json.json"
)

con = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)

genai.configure(api_key=os.getenv("GEMINI_API"))

model = genai.GenerativeModel("gemini-2.5-flash")

def normalize_url(url):
    logging.info(f"Normalizing URL: {url}")
    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower()
    normalized = urlunparse(parsed._replace(netloc=netloc))
    logging.info(f"Normalized URL: {normalized}")
    return normalized

def download_image(url, results):
    try:
        logging.info(f"Downloading image from: {url}")
        resp = requests.get(url)
        url = normalize_url(url)
        resp = requests.get(url)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        results.append({"mime_type": "image/jpeg", "data": buf.getvalue()})
        logging.info(f"Image downloaded successfully: {url}")
    except Exception as e:
        logging.error(f"Error downloading {url}: {e}")

def image_search(urls):
    logging.info("Starting image search")
    results = []
    threads = []
    for url in urls:
        thread = threading.Thread(target=download_image, args=(url, results))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    logging.info("Image search completed")
    return results

import requests

def validate_images_under_10mb(urls: list[str]) -> bool:
    """
    Check if all images in the list are under 10 MB.
    Returns True if all are valid, False if any exceeds 10MB or is invalid.
    """
    for url in urls:
        try:
            # HEAD request to check size quickly
            resp = requests.head(url, allow_redirects=True)
            resp.raise_for_status()

            size = resp.headers.get("Content-Length")
            if size is not None and int(size) > 10 * 1024 * 1024:
                return False  # too large

            # If Content-Length missing, stream to check actual size
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                downloaded = 0
                for chunk in r.iter_content(8192):
                    downloaded += len(chunk)
                    if downloaded > 10 * 1024 * 1024:
                        return False  # too large

        except Exception:
            return False  # failed to fetch or invalid URL

    return True  # All passed


def split_urls(urls_str: str):
    logging.info("Splitting URLs")
    urls_str = urls_str.strip()
    if re.search(r"\s", urls_str):
        urls = urls_str.split()
    else:
        urls = re.split(r'(?<=\.(?:jpg|JPG|png|PNG))', urls_str)
        urls = [u for u in urls if u.strip()]
    if len(urls) != 4:
        logging.error(f"Expected 4 URLs, found {len(urls)}")
        raise ValueError(f"Expected 4 URLs, found {len(urls)}")
    logging.info(f"Split URLs: {urls}")
    return urls

def safe_parse_json(text: str) -> dict:
    """
    Clean LLM output and parse as JSON safely.
    """
    try:
        # Remove markdown fences ```json ... ```
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
        cleaned = re.sub(r"```$", "", cleaned.strip())

        # Remove trailing commas before } or ]
        cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)

        return json.loads(cleaned)
    except Exception as e:
        logging.error(f"Failed to parse JSON: {e}")
        logging.debug(f"Raw text was: {text}")
        return {}

def rgb_to_basic_color(r, g, b):
    if r > 150 and g < 100 and b < 100:
        return "red"
    elif g > 150 and r < 100 and b < 100:
        return "green"
    elif b > 150 and r < 100 and g < 100:
        return "blue"
    elif r > 100 and g > 100 and b < 100:
        return "yellow"
    elif r > 100 and g > 100 and b > 100:
        return "white"
    else:
        return "black"
    
def vision_cloud_for_color(image_parts):
    start = time.time()

    color_votes = {}

    try:
        
        for content in image_parts:
            image = vision.Image(content=content["data"])
            response = client.image_properties(image=image)

            props = response.image_properties_annotation
            for color in props.dominant_colors.colors[:3]:  # top 3 per image
                rgb = (int(color.color.red), int(color.color.green), int(color.color.blue))
                color_votes[rgb] = color_votes.get(rgb, 0) + color.score

        # Pick the color with the highest total score
        best_rgb = max(color_votes, key=color_votes.get)
        best_name = rgb_to_basic_color(*best_rgb)

        print(f"Detected color: {best_name} with RGB {best_rgb}")

        end = time.time()

        return {
            "color": best_name,
            "model_used" : "Cloud Vision",
            "time" : round((end - start) * 1000, 2)

        }
    except Exception as e:
        logging.exception("Error in vision_cloud_for_color")
        raise







# result = vision_cloud_for_color(urls)
# print(result)


def metallama_model(splited_urls: str):
    start = time.time()
    try:

        prompt = """
        You are an expert fashion classifier.
        Look at all 4 photos of the SAME clothing item.
        Extract ONLY these attributes:
        - Sleeve Length (short sleeve, long sleeve, sleeveless, half sleeve)
        - Neckline (crew neck, v-neck, collared, round neck, polo, etc.)
        - Closure Type (buttons, zipper, laces, slip-on, none)

        Respond ONLY in JSON like this:
        {
          "sleeve_length": "...",
          "neckline": "...",
          "closure_type": "..."
        }
        """

        input_content = [
            {"type": "text", "text": prompt},
            *[{"type": "image_url", "image_url": {"url": url}} for url in splited_urls]
        ]

        completion = client_groq.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "user", "content": input_content}
            ],
            temperature=0,
        )

        result = completion.choices[0].message.content
        end = time.time()
        logging.info(f"LLaMA Vision response: {result}")
        return {
            "attributes": safe_parse_json(result),
            "model_used": "LLaMA 3.2 Vision (Groq)",
            "time" :  round((end - start) * 1000, 2)
        }

    except Exception as e:
        logging.exception("Error in metallama_model")
        raise

def vision_model(image_parts):
    logging.info("Running vision model")
    start = time.time()

    prompt = """
    You are a fashion attribute extractor.
    Look at ALL 4 photos of the same clothing item together.
    Return ONLY a valid JSON object with the following attributes:

    {
      "category": "string ",
      "brand": "string ",
      "material": "short descriptive phrase ",
      "condition": "new | like_new | good | fair | poor",
      "style": "short descriptive phrase",
      "gender": "male | female | unisex | kids",
      "season": "short descriptive phrase ",
      "pattern": "short descriptive phrase",
      "fit": "slim | regular | loose | oversized | other"
    }

    Rules:
    - Use evidence from ALL images before deciding.
    - If an attribute is not visible, set it to "unknown".
    - Do not add explanations or text outside the JSON.
    - Ensure the JSON is valid and complete.
    """
    response = model.generate_content([prompt] + image_parts)
    end = time.time()
    logging.info(f"Vision model response: {safe_parse_json(response.text)}")
    return {"attributes": response.text, "model_used": "Gemini 2.5 Flash" , "time" : round((end - start) * 1000, 2)}


def orchestrator(urls_str: str , id) -> dict:
    results = {}
    threads = []
    timings = {}
    gemin_time = {"time": 0}
    llama_time = {"time": 0}
    cloud_time = {"time": 0}

    urls = split_urls(urls_str)

    if validate_images_under_10mb(urls):
        image_parts = image_search(urls)

        def run_cloud():
            try:
                results["cloud"] = vision_cloud_for_color(image_parts=image_parts)
                cloud_time["time"] = results["cloud"].get("time", 0)
            except Exception:
                logging.exception("Cloud Vision failed")
                results["cloud"] = {"color": "unknown", "model_used": "Cloud Vision"}
                cloud_time["time"] = 0

        def run_gemini():
            nonlocal gemin_time
            try:
                gemini_result = vision_model(image_parts)

                if isinstance(gemini_result, dict):
                    if "attributes" in gemini_result and isinstance(gemini_result["attributes"], str):
                        results["gemini"] = safe_parse_json(gemini_result["attributes"])
                        gemin_time["time"] = gemini_result.get("time", 0)
                    else:
                        results["gemini"] = gemini_result
                        gemin_time["time"] = gemini_result.get("time", 0)
                elif isinstance(gemini_result, str):
                    results["gemini"] = safe_parse_json(gemini_result)
                    gemin_time["time"] = 0
                else:
                    results["gemini"] = {}
                    gemin_time["time"] = 0

                logging.info(f"Gemini parsed attributes (final): {results['gemini']}")
            except Exception:
                logging.exception("Gemini failed")
                results["gemini"] = {}
                gemin_time["time"] = 0

        def run_llama():
            nonlocal llama_time
            try:
                result1 = metallama_model(urls)
                results["llama"] = result1["attributes"]
                llama_time["time"] = result1.get("time", 0)
            except Exception:
                logging.exception("LLaMA failed")
                results["llama"] = {}
                llama_time["time"] = 0

        t1 = threading.Thread(target=run_cloud)
        t2 = threading.Thread(target=run_gemini)
        t3 = threading.Thread(target=run_llama)

        for t in [t1, t2, t3]:
            t.start()
        for t in [t1, t2, t3]:
            t.join()

        combined = {
            "category": results["gemini"].get("category", "unknown"),
            "brand": results["gemini"].get("brand", "unknown"),
            "color": results["cloud"].get("color", "unknown"),
            "material": results["gemini"].get("material", "unknown"),
            "condition": results["gemini"].get("condition", "unknown"),
            "style": results["gemini"].get("style", "unknown"),
            "gender": results["gemini"].get("gender", "unknown"),
            "season": results["gemini"].get("season", "unknown"),
            "pattern": results["gemini"].get("pattern", "unknown"),
            "sleeve_length": results["llama"].get("sleeve_length", "unknown"),
            "neckline": results["llama"].get("neckline", "unknown"),
            "closure_type": results["llama"].get("closure_type", "unknown"),
            "fit": results["gemini"].get("fit", "unknown"),
        }

        model_info = {
            "gemini": {
                "model": "gemini-2.5-flash",
                "latency_ms": gemin_time["time"],
                "attributes": ["category","brand","material","condition","style","gender","season","pattern","fit"]
            },
            "cloud": {
                "model": "Google Cloud Vision",
                "latency_ms": cloud_time["time"],
                "attributes": ["color"]
            },
            "llama": {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "latency_ms": llama_time["time"],
                "attributes": ["sleeve_length","neckline","closure_type"]
            },
        }

        total_time = round(
            gemin_time["time"] + cloud_time["time"] + llama_time["time"], 2
        )
        processing = {
            "status": "200 Success",
            "total_latency_ms": total_time,
            "per_model_latency": {
                "gemini": gemin_time["time"],
                "cloud": cloud_time["time"],
                "llama": llama_time["time"]
            }
        }
        ids = str(id)
        cursor = con.cursor()
        cursor.execute(
    """INSERT INTO inference_results (id, attributes, model_info, processing)
       VALUES (%s, %s, %s, %s)""",
    (ids, json.dumps(combined), json.dumps(model_info), json.dumps(processing))
)
        con.commit()
        cursor.close()
        return {
            "status": 200,
            "id": ids,
            "attributes": combined,
            "model_info": model_info,
            "processing": processing
        }
    else:
        logging.error("One or more images exceed 10MB or are invalid.")
        return {
            "status": 400,
            "id": id,
            "error": "One or more images exceed 10MB or are invalid."
        }


# def analyzer(query,session_id):
#     logging.info(f"Analyzer started for session_id: {session_id}")
#     cursor = con.cursor()
#     chat_memory = []
#     cursor.execute("""
#         SELECT user_input, attributes, llm_response
#         FROM conversations
#         WHERE session_id = %s
#         ORDER BY id ASC;
#     """, (session_id,))
#     rows = cursor.fetchall()
#     if rows:
#         for row in rows:
#             chat_memory.append({
#                 "user_input": row[0],
#                 "attributes": row[1],
#                 "llm_response": row[2]
#             })
#         history = json.dumps(chat_memory, indent=2)
#         logging.info(f"Found history with {len(rows)} rows")
#     else:
#         history = ""
#         logging.info("No history found for this session")
#     result = vision_model(query)
#     client = Groq(api_key=os.getenv("GROQ_API"))
#     prompt = f"""Improved Fashion Expert Prompt
# You are an experienced fashion consultant with expertise in clothing analysis, styling, and garment construction. Your role is to provide comprehensive, knowledgeable responses about clothing items based on their detailed attributes.
# Input Data
# You will receive a JSON object containing 13 specific attributes of a clothing item:
# json{result}
# Response Guidelines
# Completeness Requirements

# MANDATORY: Address ALL 13 attributes in your response First In a list then do anything else.
# If any attribute shows "unknown", explicitly state it as "unknown" - do not skip or omit it
# Organize your response logically, grouping related attributes when appropriate

# Communication Style

# Write in a natural, conversational tone as a knowledgeable fashion expert would

# ***IMPORTANT***
# Reflect on the attributes Multiple times before answering.
# you have to incorporate all attribute information in your response
# Just give the Attributes and After that an overview of the product DO NOT GIVE ANYTHING ELSE

# Response Structure

# Overview: Brief summary of the garment type and key characteristics

# Here is the history of our conversation so far:
# {history}
# Understand the History well so that You Know what is user is talking about if the query is a follow up question.

# Demonstrate fashion expertise through your explanations
# Connect attributes to practical considerations (comfort, durability, styling versatility)
# Maintain accuracy - if an attribute is "unknown," acknowledge this limitation
# Provide actionable insights when possible

# User Query
# Please address the following specific question while incorporating all attribute information:
# {query}
# Remember: Your response should feel like a consultation with a knowledgeable fashion expert who has thoroughly examined the garment and can speak to every aspect of its construction and characteristics.   
# """
#     logging.info("Sending prompt to Groq client")
#     completion = client.chat.completions.create(
#         messages=[
#             {
#                 "role": "user",
#                 "content": prompt,
#             }
#         ],
#         model="openai/gpt-oss-120b",
#         temperature=1,
#         max_completion_tokens=8192,
#         top_p=1,
#         stream=True,
#         stop=None
#     )
#     logging.info("Analyzer completed")
#     return completion,result
