# EthQnA 🎓📚

**EthQnA** is a reference desk assistant that quickly fetches and sorts documents from a set of sources. It then answers queries based on the retrieved set and displays the corresponding reference material along with the response. Its aim is not to directly answer a larger question you may have, but rather to be an efficient assistant that finds the content that best answers your question.

## Overview 🚀

- **Reference Desk Assistant:** EthQnA rapidly gathers and sorts documents from multiple sources.
- **Query-Based Answers:** It responds to your queries by providing the most relevant documents along with the answer.
- **Efficient Content Finder:** EthQnA acts as an assistant to find the content that best answers your question, not as a complete solution provider.

## Features ✨

- Fast document retrieval and sorting.
- Query-based responses with reference material.
- Integrated Google OAuth authentication (only ethereum.org accounts allowed) for the frontend.
- Secure backend with Basic Authentication.
- Dockerized for easy deployment.
- Multiple PDF sources with relevance-based ordering (coming soon).

## Installation 🛠️

1. **Clone the repository:**

```bash
git clone https://github.com/Ramshreyas/ethqna.git
cd ethqna
```

2. **Create a .env file** in the root of the project with your configuration:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_OAUTH_CLIENT_ID=your_google_oauth_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_google_oauth_client_secret_here
ADMIN_USERNAME=your_admin_username_here
ADMIN_PASSWORD=your_admin_password_here
```

3. **Build and run the project using Docker Compose**:

```bash
docker-compose up --build -d
```

## Usage 🔧

    Frontend:
    Visit https://ethqnaxyz (replace with your domain) to access EthQnA. You'll be prompted to log in using your Google account (only ethereum.org emails are accepted).

    Backend:
    The backend API is secured with Basic Authentication. It offers endpoints such as /chat, /pdf, and others for document management.

## Contributing 🤝

Contributions are welcome! If you have suggestions or improvements, please open an issue or submit a pull request.

## License 📄

This project is MIT Licensed.

## Acknowledgments 🙏

    Built with Flask, FastAPI, and Docker.