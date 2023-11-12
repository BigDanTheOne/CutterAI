from openai import OpenAI
import openai

def yt_text_to_quiz(content):
  client = OpenAI(api_key='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')

  with open('utiles/quiz_yt_promt.txt') as f:
      promt = "".join(f.readlines())

  response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
      {"role": "system", "content": promt},
      {"role": "user", "content": content},
    ],
    temperature=0.1,
    max_tokens=1024
  )
  return response.choices[0].message.content


def doc_text_to_quiz(content):
  client = OpenAI(api_key='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')

  with open('utiles/quiz_promt.txt') as f:
      promt = "".join(f.readlines())

  response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
      {"role": "system", "content": promt},
      {"role": "user", "content": content},
    ],
    temperature=0.1,
    max_tokens=1024
  )
  return response.choices[0].message.content
