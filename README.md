Hello! Welcome to a simple info about my first web app!

This is my final project for Harvard's CS50X - "Ian's Chat Analysis Tool"

It is a simple web app that allows users to analyse their WhatsApp chat to see intresting datas about their chat history with their texter by simply clicking the Analyse button that processes their WhatsApp chat log. 

To export WhatsApp chat log: https://faq.whatsapp.com/android/chats/how-to-save-your-chat-history/

The app send the chat log to the Python Flask server through AJAX in which the server uses regular expression to parse each messages and then analysed using Pandas library. The requested analysis is then processed by the client's web browser to visualise the chat data analysis using Chart.Js library. 