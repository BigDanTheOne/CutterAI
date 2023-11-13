from openai import OpenAI
import openai

def text_to_summary(content):
  client = OpenAI(api_key='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')

  with open('utiles/summary_promt.txt') as f:
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

  with open('utiles/summary_promt.txt') as f:
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

  with open('utiles/summary_promt.txt') as f:
    promt = "".join(f.readlines())

  response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=chat_history,
    temperature=0,
    stream=True
  )
  return response
