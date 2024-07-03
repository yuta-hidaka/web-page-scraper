from openai import OpenAI

class GPT:
    def __init__(self, model_name, api_key):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def base64_image_to_astro_tailwind_code(self, imageBase64):
        print("base64_image_to_astro_tailwind_code request start")
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional front end software engineer assistant, skilled in explaining complex programming concepts with creative flair.",
                    },
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": """
                        ### There are condition ###
                        1. Read given image top to bottom carefully and "don't miss any information"
                        2. Write code based on Astro and Tailwind.
                        3. You must include icons and images in source code.
                        4. For fake images please use placehold.co
                        5. Not use component.
                        6. Make sure header and footer is included
                        7. Respond with only the code without explanation.
                        8. The file should contain all images data
                        9. The color should be respect original images, if there are no color on Tailwind default, use RGB color
                        10. Do not use markdown
                        """},
                        {
                            "type": "image_url", 
                            "image_url": 
                            {
                                "url": f"data:image/png;base64,{imageBase64}"
                            }
                        }
                    ],
                }
            ]
        )   
        print("base64_image_to_astro_tailwind_code request done")
        print("code: ", resp.choices[0].message.content)

        if resp.choices[0].message.content.startswith("```astro"):
            return resp.choices[0].message.content.split("```astro")[1].split("```")[0]

        if resp.choices[0].message.content.startswith("```html"):
            return resp.choices[0].message.content.split("```html")[1].split("```")[0]

        return resp.choices[0].message.content