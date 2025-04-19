Create a "Hello World" app and run it
Create a file named app.py in your project folder.
import streamlit as st

st.write("Hello world")
Any time you want to use your new environment, you first need to go to your project folder (where the .venv directory lives) and run the command to activate it:
# Windows command prompt
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS and Linux
source .venv/bin/activate
Once activated, you will see your environment's name in parentheses at the beginning of your terminal prompt. "(.venv)"

Run your Streamlit app.

streamlit run app.py
If this doesn't work, use the long-form command:

python -m streamlit run app.py
To stop the Streamlit server, press Ctrl+C in the terminal.

When you're done using this environment, return to your normal shell by typing:

deactivate