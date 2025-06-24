orchestrator-1 | Available
models: ['codex-mini-latest', 'gpt-4o-2024-05-13', 'gpt-4o-mini-2024-07-18', 'gpt-4o-2024-08-06', 'gpt-4o-2024-11-20', 'gpt-4.5-preview-2025-02-27', 'gpt-4.1-2025-04-14', 'gpt-4.1-mini-2025-04-14', 'gpt-4.1-nano-2025-04-14']
orchestrator-1 | Response from OpenAI: UnknownAgent
orchestrator-1 | Invalid response: Error
orchestrator-1 | Available
models: ['codex-mini-latest', 'gpt-4o-2024-05-13', 'gpt-4o-mini-2024-07-18', 'gpt-4o-2024-08-06', 'gpt-4o-2024-11-20', 'gpt-4.5-preview-2025-02-27', 'gpt-4.1-2025-04-14', 'gpt-4.1-mini-2025-04-14', 'gpt-4.1-nano-2025-04-14']
orchestrator-1 | Response from OpenAI: UnknownAgent
orchestrator-1 | Invalid response: Error
orchestrator-1 | Available
models: ['codex-mini-latest', 'gpt-4o-2024-05-13', 'gpt-4o-mini-2024-07-18', 'gpt-4o-2024-08-06', 'gpt-4o-2024-11-20', 'gpt-4.5-preview-2025-02-27', 'gpt-4.1-2025-04-14', 'gpt-4.1-mini-2025-04-14', 'gpt-4.1-nano-2025-04-14']
orchestrator-1 | Response from OpenAI: UnknownAgent
orchestrator-1 | Invalid response: Error
orchestrator-1 | Failed to generate successful product variations after retries.
orchestrator-1 | INFO:     172.19.0.1:46964 - "POST /route HTTP/1.1" 500 Internal Server Error
orchestrator-1 | ERROR:    Exception in ASGI application
orchestrator-1 | Traceback (most recent call last):
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
orchestrator-1 | result = await app(  # type: ignore[func-returns-value]
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
orchestrator-1 | return await self.app(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/fastapi/applications.py", line 1054, in __call__
orchestrator-1 | await super().__call__(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/applications.py", line 112, in __call__
orchestrator-1 | await self.middleware_stack(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/middleware/errors.py", line 187, in __call__
orchestrator-1 | raise exc
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/middleware/errors.py", line 165, in __call__
orchestrator-1 | await self.app(scope, receive, _send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/middleware/cors.py", line 93, in __call__
orchestrator-1 | await self.simple_response(scope, receive, send, request_headers=headers)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/middleware/cors.py", line 144, in
simple_response
orchestrator-1 | await self.app(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
orchestrator-1 | await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
orchestrator-1 | raise exc
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
orchestrator-1 | await app(scope, receive, sender)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 714, in __call__
orchestrator-1 | await self.middleware_stack(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 734, in app
orchestrator-1 | await route.handle(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 288, in handle
orchestrator-1 | await self.app(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 76, in app
orchestrator-1 | await wrap_app_handling_exceptions(app, request)(scope, receive, send)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
orchestrator-1 | raise exc
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
orchestrator-1 | await app(scope, receive, sender)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/starlette/routing.py", line 73, in app
orchestrator-1 | response = await f(request)
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/fastapi/routing.py", line 301, in app
orchestrator-1 | raw_response = await run_endpoint_function(
orchestrator-1 | File "/usr/local/lib/python3.9/site-packages/fastapi/routing.py", line 212, in run_endpoint_function
orchestrator-1 | return await dependant.call(**values)
orchestrator-1 | File "/app/main.py", line 102, in route
orchestrator-1 | response = strip_outer_quotes(response)
orchestrator-1 | File "/app/main.py", line 67, in strip_outer_quotes
orchestrator-1 | s = s.strip()
orchestrator-1 | AttributeError: 'dict' object has no attribute 'strip'