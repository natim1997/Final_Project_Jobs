import streamlit as st
import requests

# simple english comment: Setup page configuration and title
st.set_page_config(page_title="JobMatcher AI", page_icon="🎯", layout="centered")

st.title("🎯 JobMatcher AI - Prototype")
st.write("Enter a candidate ID to get real-time AI job matches from the cloud.")

# simple english comment: Input field for the candidate ID
candidate_id = st.text_input("Candidate ID:", placeholder="e.g., cand_netanel_1997")

# simple english comment: Button to trigger the search
if st.button("Find Matches 🚀"):
    if not candidate_id:
        st.warning("Please enter a Candidate ID first.")
    else:
        # simple english comment: Show a loading spinner while waiting for the cloud
        with st.spinner('Analyzing profile and fetching AI matches from Cloud...'):
            try:
                # simple english comment: Call the deployed Node.js backend
                api_url = f"https://node-backend-493713788422.me-west1.run.app/api/matches/{candidate_id}"
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get("matches", [])
                    
                    if not matches:
                        st.info("No matches found for this candidate.")
                    else:
                        st.success(f"Found {len(matches)} potential matches!")
                        
                        # simple english comment: Display each match in a nice visual card
                        for match in matches:
                            with st.container():
                                st.subheader(f"🏢 {match['job_title']} at {match['company_name']}")
                                
                                # simple english comment: Use columns to display score and details side-by-side
                                col1, col2 = st.columns([1, 3])
                                
                                with col1:
                                    st.metric(label="AI Match Score", value=f"{match['final_match_score']}%")
                                
                                with col2:
                                    st.write(f"**Explanation:** {match['match_explanation']}")
                                    st.write(f"**Distance:** {match['distance_km']} km")
                                
                                # simple english comment: Collapsible section for extra job details
                                with st.expander("View Job Description"):
                                    st.write(match['full_job_data']['description'])
                                
                                st.divider() # simple english comment: Visual line between matches
                                
                else:
                    st.error(f"Error from server: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Failed to connect to the server. Error: {e}")