
#import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx,get_script_run_ctx
from subprocess import Popen

ctx = get_script_run_ctx()
##Some code##
process = Popen(['python','PythonApplication1.py'])
add_script_run_ctx(process,ctx)