- '/Users/dhruvmiyani/Downloads/Eloquent AI - AI Engineer Technical Assignment_ AI-Powered Chatbot Challenge (1) (1) (1) (1).pdf'
- Eloquent AI
AI Engineer Technical Assignment: AI-Powered Chatbot Challenge
Overview
The goal of this assignment is to assess your ability to design, implement, and deploy a
full-stack web application that features an AI-powered chatbot using retrieval-augmented
generation (RAG). The chatbot should retrieve relevant context from a knowledge base
before generating responses, reducing hallucinations and improving answer accuracy.
This challenge evaluates your skills in TypeScript, Python, AWS, API design, full-stack
development, and deployment best practices.
Problem Statement
In real-world applications, AI chatbots often struggle with accuracy due to
hallucinations—they generate plausible but incorrect information. To address this, you will
implement a chatbot that enhances a language model with retrieval-augmented generation
(RAG), allowing it to fetch relevant data from a vector database before responding to user
queries.
Your task is to build a web application where users can interact with this AI chatbot in a
persisted chat environment, supporting both authenticated and anonymous users. The
system should be scalable, capable of handling multiple chat sessions, and designed for
deployment in AWS.
The bot will answer questions about the FAQs of an imaginary fintech company, covering the
most common questions users might have about creating and verifying an account, managing
payments and transfers, keeping their accounts secure, and understanding financial
regulations. It is organized into five main categories—Account & Registration, Payments &
Transactions, Security & Fraud Prevention, Regulations & Compliance, and Technical Support
& Troubleshooting—to provide comprehensive guidance on everything from setting up an
account to addressing fraud concerns and technical glitches.
Assignment Scope & Requirements
1. Backend (Python + FastAPI)
● Implement the backend using FastAPI.
● Design and expose RESTful APIs to handle chat functionality.
● Implement retrieval-augmented generation (RAG) by integrating the Pinecone vector
database:

2. Frontend (TypeScript + React/Next.js)
● Develop the frontend using React or Next.js.
● Design a clean and intuitive chat UI where users can interact with the chatbot.
● Implement chat history persistence so users can view previous conversations.
● If you want to have some UI inspiration, you can use OpenAI ChatGPT interface
3. Chat Functionality (RAG & Persistence)
● Enable users to enter questions and receive AI-generated responses.
● Retrieve relevant information from the knowledge base before generating answers.
● Store and retrieve chat history efficiently, allowing users to scroll back and reference
past interactions.
4. User Management
● Let’s call first time users anonymous. These are users that opened the WebApp for
the first time.
● Support returning users, these are users that by returning to the platform they are
now known users to the system. They may have a chat history.
● Consider JWT-based authentication or another modern authentication approach.
5. Deploy Ready for AWS
● Ensure the application is production-ready

● Design on paper what you would use to deploy this WebApp on AWS.
● Follow best DevOps practices, including proper environment configuration.
Evaluation Criteria
Your submission will be evaluated based on the following:
1. Code Quality & Best Practices
● Clean, maintainable, and well-documented code.
● Proper use of TypeScript and Python best practices.
2. Full-Stack Implementation
● Well-structured frontend and backend components.
● Efficient API design for chat functionality.
3. Retrieval-Augmented Generation (RAG) Implementation
● Effective integration of Pinecone for knowledge retrieval.
● Accurate chatbot responses using contextual data.
4. Chat Persistence & Scalability
● Proper storage and retrieval of chat history.
● Scalable design to handle multiple chat sessions.
5. User Experience
● Seamless authentication for registered users.
● Smooth user experience, including UI responsiveness and chat history navigation.
6. AWS Deployment & DevOps Best Practices
● Thoughtful AWS deployment strategy.
● Use of environment configurations, and scalability considerations.
Submission Guidelines
● Share your GitHub repository with clear README instructions on how to run your
application locally.
● Include a brief write-up on how you approached the problem and any architectural
decisions you made. -> follow as writtern in doc