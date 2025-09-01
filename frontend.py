import streamlit as st
import requests
import json
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Clothing Analysis Tool",
    page_icon="👔",
    layout="wide"
)

# App title
st.title("👔 Clothing Analysis Tool")
st.markdown("Upload 4 image URLs of the same clothing item to get detailed analysis")

# API configuration
API_BASE_URL = "https://minimal-multi-model-service-712257844272.us-south1.run.app"  # Change this to your FastAPI server URL

def call_analysis_api(urls_text):
    """Call the FastAPI analysis endpoint"""
    try:
        payload = {"query": urls_text}
        response = requests.post(
            f"{API_BASE_URL}/v1/items/analyze",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server. Make sure your FastAPI server is running on http://localhost:8000")
        return None
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. The analysis is taking too long.")
        return None
    except Exception as e:
        st.error(f"❌ Error calling API: {str(e)}")
        return None

def display_attributes(attributes):
    """Display clothing attributes in a nice format"""
    st.subheader("📋 Clothing Attributes")
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Basic Information:**")
        st.write(f"• **Category:** {attributes.get('category', 'unknown')}")
        st.write(f"• **Brand:** {attributes.get('brand', 'unknown')}")
        st.write(f"• **Material:** {attributes.get('material', 'unknown')}")
        st.write(f"• **Condition:** {attributes.get('condition', 'unknown')}")
        st.write(f"• **Gender:** {attributes.get('gender', 'unknown')}")
        st.write(f"• **Season:** {attributes.get('season', 'unknown')}")
        st.write(f"• **Fit:** {attributes.get('fit', 'unknown')}")
    
    with col2:
        st.markdown("**Design Details:**")
        st.write(f"• **Color:** {attributes.get('color', 'unknown')}")
        st.write(f"• **Style:** {attributes.get('style', 'unknown')}")
        st.write(f"• **Pattern:** {attributes.get('pattern', 'unknown')}")
        st.write(f"• **Sleeve Length:** {attributes.get('sleeve_length', 'unknown')}")
        st.write(f"• **Neckline:** {attributes.get('neckline', 'unknown')}")
        st.write(f"• **Closure Type:** {attributes.get('closure_type', 'unknown')}")

def display_model_info(model_info, processing):
    """Display model performance information"""
    st.subheader("🤖 Model Performance")
    
    # Total processing time
    total_time = processing.get('total_latency_ms', 0)
    st.metric("Total Processing Time", f"{total_time} ms")
    
    # Model breakdown
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Gemini 2.5 Flash**")
        gemini_time = processing.get('per_model_latency', {}).get('gemini', 0)
        st.write(f"⏱️ {gemini_time} ms")
        st.write("📝 Category, Brand, Material, etc.")
    
    with col2:
        st.markdown("**Google Cloud Vision**")
        cloud_time = processing.get('per_model_latency', {}).get('cloud', 0)
        st.write(f"⏱️ {cloud_time} ms")
        st.write("🎨 Color Detection")
    
    with col3:
        st.markdown("**LLaMA Vision**")
        llama_time = processing.get('per_model_latency', {}).get('llama', 0)
        st.write(f"⏱️ {llama_time} ms")
        st.write("👕 Sleeve, Neckline, Closure")

def main():
    # Input section
    st.subheader("📤 Input Image URLs")
    st.markdown("Please provide 4 image URLs of the same clothing item (one URL per line or space-separated)")
    
    # Text area for URLs
    urls_input = st.text_area(
        "Image URLs:",
        height=150,
        placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.jpg\nhttps://example.com/image3.jpg\nhttps://example.com/image4.jpg"
    )
    
    # Analyze button
    if st.button("🔍 Analyze Clothing", type="primary"):
        if not urls_input.strip():
            st.warning("⚠️ Please enter image URLs")
            return
        
        # Show loading spinner
        with st.spinner("🔄 Analyzing clothing... This may take a few moments"):
            result = call_analysis_api(urls_input.strip())
        
        if result:
            # Check if analysis was successful
            if result.get('status') == 200:
                st.success("✅ Analysis completed successfully!")
                
                # Display attributes
                if 'attributes' in result:
                    display_attributes(result['attributes'])
                
                # Display model performance
                if 'model_info' in result and 'processing' in result:
                    display_model_info(result['model_info'], result['processing'])
                
                # Show raw JSON in expander for debugging
                with st.expander("🔧 Raw JSON Response"):
                    st.json(result)
                    
            else:
                st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        
    # Instructions section
    st.sidebar.header("📖 Instructions")
    st.sidebar.markdown("""
    **How to use:**
    
    1. Prepare 4 image URLs of the same clothing item
    2. Paste them in the text area (one per line or space-separated)
    3. Click 'Analyze Clothing'
    4. Wait for the multi-model analysis to complete
    
    **Requirements:**
    - Exactly 4 image URLs
    - Each image must be under 10MB
    - Images should show the same clothing item from different angles
    - URLs must be publicly accessible
    
    **Supported formats:**
    - JPG, JPEG, PNG
    """)
    
    # API Status
    st.sidebar.header("🔗 API Status")
    if st.sidebar.button("Check API Connection"):
        try:
            response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
            if response.status_code == 200:
                st.sidebar.success("✅ API is running")
            else:
                st.sidebar.error("❌ API returned error")
        except:
            st.sidebar.error("❌ Cannot connect to API")

if __name__ == "__main__":
    main()
