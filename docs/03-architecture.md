**Technical Architecture**

**Scope**
MVP Slice. Items in the Won't column are not shown


**Stack**

Choice | Serves | Downsides
Streamlit (Python) | Fr-2 Fr-3 | Limited control over layout
Streamlit Community Cloud | Live URL | Free apps sleep when idle, first load is slow
Supabase | Fr-3 Fr-4 Fr-5 | Health data and journal text live on third-party server
Oura API | Fr-1 | Requires an active membership 
Claude API | Fr-2 Fr-4 | Costs money per call. Sees journal text only, never Oura data (Oura agreement Sec. 4(d)) 

**Trace:**

1. Browser -> Streamlit: I open the app on my phone
2. Streamlit -> Supabase: The app checks my login and loads my Oura token 
3. Streamlit -> Oura: The app fetches today's readiness and sleep scores, and saves them
4. Streamlit: App code picks tonight's 3 to 5 questions from a fixed set, using today's scores. Nothing is sent to Claude in this step
5. Browser -> Streamlit: I answer the questions and submit 
6. Streamlit -> Claude: The app sends only my written answers (no Oura data) and gets back tags (caffeine, stress, etc.)
7. Streamlit -> Supabase: The app saves the entry and tags, and links yesterday's entry to last night's sleep 
8. Streamlit -> Browser: I see a confirmation. 
9. Streamlit: Trends and correlations are computed and worded by app code from templates, each with its number of nights. Claude is not involved 

