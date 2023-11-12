from openai import OpenAI
import openai

def text_to_summary(content):
  client = OpenAI(api_key='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')

  with open('utiles/promt.txt') as f:
      promt = "".join(f.readlines())

  response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
      {"role": "system", "content": promt},
      {"role": "user", "content": content},
    ],
    temperature=0,
    max_tokens=1024
  )
  return response.choices[0].message.content


def text_to_summary_in_parts(content):
  client = OpenAI(api_key='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')

  with open('utiles/promt.txt') as f:
    promt = "".join(f.readlines())

  response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
      {"role": "system", "content": promt},
      {"role": "user", "content": content},
    ],
    temperature=0,
    stream=True
  )
  return response


def ask_question_gpt(chat_history):
  client = OpenAI(api_key='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')

  with open('utiles/promt.txt') as f:
    promt = "".join(f.readlines())

  response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=chat_history,
    temperature=0,
    stream=True
  )
  return response
