# language-2-software
Casusproject minor Software Architecture Blok 4 2024-2025 Zuyd Hogeschool

Monorepo for the different services and components for the Proof of Concept.
Each component or service has it's own subfolder where all the code and dockerfile lives.

## Setup

Before running, make sure you have a .env file in the root of this repository.
It should contain the following variables, make sure you give them proper values.

```
OPENAI_API_KEY=<string>
MAX_RETRY=<number>
LOGFIRE_WRITE_TOKEN=<string> | OPTIONAL
```

## Running the stack

Build the stack before starting it.

```
docker compose build
```

Now start the stack.

```
docker compose up
```
