from openai import OpenAI
import openai

def explaine(content):
  client = OpenAI(api_key='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')

  with open('utiles/quiz_yt_promt.txt') as f:
      promt = "".join(f.readlines())

  response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": promt},
      {"role": "user", "content": content},
    ],
    temperature=0,
    max_tokens=1024
  )
  return response.choices[0].message.content