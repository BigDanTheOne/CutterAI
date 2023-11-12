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
  collected_chunks = []
  collected_messages = []
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
  for chunk in response:
    collected_chunks.append(chunk)  # save the event response
    chunk_message = chunk['choices'][0]['delta']  # extract the message
    collected_messages.append(chunk_message)  # save the message
  full_reply_content = ''.join([m.get('content', '') for m in collected_messages])
  return full_reply_content
