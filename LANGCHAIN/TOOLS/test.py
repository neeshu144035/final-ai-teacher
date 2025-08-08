import google.generativeai as genai

genai.configure(api_key="AIzaSyBV6Vl8SvGMYyhaJDisF8zDYWa_7PZ82Lc")

for m in genai.list_models():
    print(m.name)
