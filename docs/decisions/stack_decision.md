**Stack Decision: Streamlit + Supabase**

**Context:** The app has to work on my phone at bedtime, be live by December, and keep the Claude and Oura keys secret. 

**Decision:** Streamlit on Streamlit Community Cloud, Supabase for the database and login. 

**Why not others:** Flutter + Supabase is also something I considered, but hiding the keys would mean writing edge functions which I would have to learn. Streamlit runs on the server, I understand how it works, and the keys stay hidden. 

**What would change my mind:** If Streamlit is too hard to use on my phone after the UI lab on October 29.