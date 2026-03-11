"""
Mistral AI service for code analysis and incident solutions.
Provides intelligent code review and incident response recommendations.
Supports CLI-like commands for running tests and finding errors.
"""
import logging
import re
import subprocess
import asyncio
from typing import Optional, Dict, Any, Tuple
import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)


class MistralService:
    """Service for interacting with Mistral AI API with CLI command support"""
    
    def __init__(self):
        """Initialize Mistral service with API key from settings"""
        self.api_key = settings.mistral_api_key
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not found in environment. Code analysis will not be available.")
            self.enabled = False
            return
        
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = "mistral-large-latest"  # or "mistral-medium" for faster responses
        self.enabled = True
        
        # CLI command patterns
        self.cli_commands = {
            r'^/run\s+(.+)$': self._execute_command,
            r'^/test\s*(.*)$': self._run_tests,
            r'^/lint\s*(.*)$': self._run_linter,
            r'^/errors?\s*(.*)$': self._find_errors,
            r'^/build\s*(.*)$': self._run_build,
            r'^/help$': self._show_help,
            r'^/task\s+(.+)$': self._delegate_task,
            r'^/agents?$': self._list_agents,
            r'^/status\s*(.*)$': self._check_task_status,
        }
        
        logger.info("Mistral AI service initialized successfully with CLI support")
    
    async def analyze_code(
        self,
        repository_name: str,
        code_snippet: Optional[str] = None,
        file_path: Optional[str] = None,
        question: Optional[str] = None
    ) -> Optional[str]:
        """
        Analyze code and provide insights.
        Supports CLI-like commands starting with /:
        - /run <command> - Execute a shell command
        - /test [path] - Run tests
        - /lint [path] - Run linter
        - /errors [path] - Find errors in code
        - /build [target] - Run build command
        - /help - Show available commands
        
        Args:
            repository_name: Name of the repository
            code_snippet: Code to analyze (optional)
            file_path: Path to the file being analyzed (optional)
            question: Specific question about the code (optional)
            
        Returns:
            Analysis result or None if generation fails
        """
        if not self.enabled:
            logger.warning("Mistral AI is not enabled. Cannot analyze code.")
            return None
        
        try:
            # Check if question is a CLI command
            if question:
                for pattern, handler in self.cli_commands.items():
                    match = re.match(pattern, question.strip(), re.IGNORECASE)
                    if match:
                        # Execute CLI command
                        command_result = await handler(match, repository_name)
                        return command_result
                
                # Check for interactive question patterns
                if any(phrase in question.lower() for phrase in ['what should i', 'which approach', 'how should i choose', 'what would you recommend']):
                    # Generate interactive questions
                    questions = await self._generate_interactive_questions(question, repository_name)
                    if questions:
                        return await self.ask_user_question(questions, repository_name)
            
            # Regular code analysis
            prompt = self._build_code_analysis_prompt(
                repository_name=repository_name,
                code_snippet=code_snippet,
                file_path=file_path,
                question=question
            )
            
            return await self._call_mistral_api(prompt)
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return None
    
    async def suggest_incident_solution(
        self,
        repository_name: str,
        incident_description: str,
        error_logs: Optional[str] = None,
        recent_changes: Optional[str] = None
    ) -> Optional[str]:
        """
        Suggest solutions for incidents based on repository context.
        
        Args:
            repository_name: Name of the repository
            incident_description: Description of the incident
            error_logs: Error logs if available (optional)
            recent_changes: Recent code changes (optional)
            
        Returns:
            Suggested solutions or None if generation fails
        """
        if not self.enabled:
            logger.warning("Mistral AI is not enabled. Cannot suggest solutions.")
            return None
        
        try:
            prompt = self._build_incident_solution_prompt(
                repository_name=repository_name,
                incident_description=incident_description,
                error_logs=error_logs,
                recent_changes=recent_changes
            )
            
            return await self._call_mistral_api(prompt)
            
        except Exception as e:
            logger.error(f"Error suggesting incident solution: {e}")
            return None
    
    async def review_security(
        self,
        repository_name: str,
        code_snippet: Optional[str] = None
    ) -> Optional[str]:
        """
        Review code for security vulnerabilities.
        
        Args:
            repository_name: Name of the repository
            code_snippet: Code to review (optional)
            
        Returns:
            Security review or None if generation fails
        """
        if not self.enabled:
            logger.warning("Mistral AI is not enabled. Cannot review security.")
            return None
        
        try:
            prompt = self._build_security_review_prompt(
                repository_name=repository_name,
                code_snippet=code_snippet
            )
            
            return await self._call_mistral_api(prompt)
            
        except Exception as e:
            logger.error(f"Error reviewing security: {e}")
            return None
    
    async def ask_user_question(self, questions: list, repository_name: str) -> str:
        """
        Ask interactive user questions with multiple choice options.
        This simulates the Mistral Vibe interactive question feature.
        """
        try:
            # Format questions for display
            formatted_questions = []
            for i, q in enumerate(questions):
                question_text = f"**Question {i+1}:** {q.get('question', '')}\n\n"
                
                options = q.get('options', [])
                for j, option in enumerate(options):
                    question_text += f"{j+1}. **{option.get('label', '')}** - {option.get('description', '')}\n"
                
                # Add "Other" option
                question_text += f"{len(options)+1}. **Other** - Provide your own answer\n"
                formatted_questions.append(question_text)
            
            result = "🤔 **I need your input to provide the best guidance:**\n\n"
            result += "\n---\n\n".join(formatted_questions)
            result += "\n---\n\n💡 **Please respond with the number of your choice or provide your own answer.**"
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting user questions: {e}")
            return "I'd like to ask you some questions to better understand your needs, but encountered an error formatting them."
    
    async def delegate_task(self, task_description: str, agent_type: str, repository_name: str) -> str:
        """
        Delegate tasks to specialized subagents like Mistral Vibe.
        """
        try:
            # Import here to avoid circular imports
            from .subagent_service import subagent_service
            
            # Delegate to subagent service
            task_id = await subagent_service.delegate_task(
                task_description=task_description,
                agent_type=agent_type,
                repository_name=repository_name
            )
            
            return f"🤖 **Task Delegated Successfully**\n\nI've assigned this task to the **{agent_type}** subagent.\n\n**Task ID:** `{task_id}`\n**Description:** {task_description}\n\nThe subagent is working on this independently. You can check the progress or continue with other tasks. I'll integrate the results when complete.\n\n*This allows me to handle multiple tasks in parallel while keeping our conversation focused.*"
            
        except Exception as e:
            logger.error(f"Error delegating task: {e}")
            return f"❌ **Task Delegation Failed**\n\nI encountered an error while trying to delegate the task: {str(e)}\n\nLet me handle this directly instead."
    
    async def _generate_interactive_questions(self, user_question: str, repository_name: str) -> list:
        """Generate interactive questions based on user query"""
        try:
            # Get project context for better questions
            project_context = await project_context_service.get_project_context(repository_name)
            tech_stack = project_context.get('tech_stack', {})
            
            questions = []
            
            if 'testing' in user_question.lower():
                questions.append({
                    "question": "What's your primary testing goal?",
                    "options": [
                        {"label": "Unit Testing", "description": "Test individual functions and components"},
                        {"label": "Integration Testing", "description": "Test how components work together"},
                        {"label": "E2E Testing", "description": "Test complete user workflows"},
                        {"label": "Performance Testing", "description": "Test speed and load handling"}
                    ]
                })
                
                if 'React' in tech_stack.get('frameworks', []):
                    questions.append({
                        "question": "Which React testing approach interests you most?",
                        "options": [
                            {"label": "Component Testing", "description": "Test React components in isolation"},
                            {"label": "Hook Testing", "description": "Test custom React hooks"},
                            {"label": "User Interaction", "description": "Test clicks, forms, and user flows"}
                        ]
                    })
            
            elif 'security' in user_question.lower():
                questions.append({
                    "question": "Which security area is your priority?",
                    "options": [
                        {"label": "Authentication", "description": "Login, tokens, and user verification"},
                        {"label": "Data Protection", "description": "Encryption, storage, and transmission"},
                        {"label": "Input Validation", "description": "Preventing injection attacks"},
                        {"label": "Dependencies", "description": "Third-party package vulnerabilities"}
                    ]
                })
            
            elif 'architecture' in user_question.lower() or 'design' in user_question.lower():
                questions.append({
                    "question": "What architectural aspect needs attention?",
                    "options": [
                        {"label": "Code Organization", "description": "File structure and module organization"},
                        {"label": "Design Patterns", "description": "Applying proven architectural patterns"},
                        {"label": "Scalability", "description": "Preparing for growth and load"},
                        {"label": "Maintainability", "description": "Making code easier to modify"}
                    ]
                })
            
            elif 'performance' in user_question.lower():
                questions.append({
                    "question": "Which performance area concerns you most?",
                    "options": [
                        {"label": "Frontend Performance", "description": "Page load times and user experience"},
                        {"label": "Backend Performance", "description": "API response times and throughput"},
                        {"label": "Database Performance", "description": "Query optimization and indexing"},
                        {"label": "Memory Usage", "description": "Reducing memory consumption"}
                    ]
                })
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating interactive questions: {e}")
            return []
    
    async def _call_mistral_api(self, prompt: str) -> Optional[str]:
        """Call Mistral AI API with the given prompt"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are CloudHelm Assistant, an expert SRE and DevOps AI assistant. You are like Mistral's open-source CLI coding assistant - conversational, intelligent, and helpful.

Your personality:
- Conversational and friendly, like talking to a knowledgeable colleague
- Provide context and explanations, not just commands
- Offer insights about code quality, best practices, and potential issues
- Suggest improvements and alternatives
- Explain the "why" behind recommendations

When users ask about testing, linting, or code analysis:
- Provide intelligent analysis and recommendations
- Explain what to look for and why it matters
- Suggest specific improvements
- Offer best practices and tips
- Be educational and insightful

You can execute commands when specifically requested with /command syntax, but primarily focus on being a knowledgeable coding companion who provides valuable insights and guidance."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get("choices"):
                    logger.error("Mistral returned no choices")
                    return None
                
                message = data["choices"][0].get("message", {})
                content = message.get("content", "")
                
                if not content:
                    logger.error("Mistral returned empty content")
                    return None
                
                logger.info("Successfully generated response from Mistral AI")
                return content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Mistral API: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling Mistral API: {e}")
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are CloudHelm Assistant, an expert SRE and DevOps AI assistant. You are like Mistral's open-source CLI coding assistant - conversational, intelligent, and helpful.

Your personality:
- Conversational and friendly, like talking to a knowledgeable colleague
- Provide context and explanations, not just commands
- Offer insights about code quality, best practices, and potential issues
- Suggest improvements and alternatives
- Explain the "why" behind recommendations

When users ask about testing, linting, or code analysis:
- Provide intelligent analysis and recommendations
- Explain what to look for and why it matters
- Suggest specific improvements
- Offer best practices and tips
- Be educational and insightful

You can execute commands when specifically requested with /command syntax, but primarily focus on being a knowledgeable coding companion who provides valuable insights and guidance."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get("choices"):
                    logger.error("Mistral returned no choices")
                    return None
                
                message = data["choices"][0].get("message", {})
                content = message.get("content", "")
                
                if not content:
                    logger.error("Mistral returned empty content")
                    return None
                
                logger.info("Successfully generated response from Mistral AI")
                return content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Mistral API: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling Mistral API: {e}")
            return None
    
    def _build_code_analysis_prompt(
        self,
        repository_name: str,
        code_snippet: Optional[str],
        file_path: Optional[str],
        question: Optional[str]
    ) -> str:
        """Build prompt for code analysis"""
        
        context = f"I'm working on the **{repository_name}** repository"
        if file_path:
            context += f" and looking at `{file_path}`"
        context += ".\n\n"
        
        if code_snippet:
            context += f"Here's the code I'm working with:\n```\n{code_snippet}\n```\n\n"
        
        if question:
            if question.lower() in ["test", "testing", "run tests"]:
                context += f"**Question:** {question}\n\n"
                context += """I'd like to understand the testing strategy for this codebase. Can you help me with:

1. **Testing Approach**: What testing frameworks and strategies would work best for this project?
2. **Test Coverage**: What areas should I focus on testing first?
3. **Best Practices**: Any specific testing patterns or practices you'd recommend?
4. **Common Issues**: What are typical testing challenges I might encounter?

Please provide insights and recommendations rather than just running commands."""
            
            elif question.lower() in ["lint", "linting", "code quality"]:
                context += f"**Question:** {question}\n\n"
                context += """I want to improve the code quality in this repository. Can you help me understand:

1. **Code Quality**: What potential issues should I look for in this codebase?
2. **Best Practices**: What coding standards and practices would you recommend?
3. **Tools**: What linting tools and configurations would work best?
4. **Common Problems**: What are typical code quality issues in projects like this?

Please provide analysis and recommendations for maintaining high code quality."""
            
            elif question.lower() in ["errors", "debugging", "issues"]:
                context += f"**Question:** {question}\n\n"
                context += """I'm looking to identify and resolve potential issues in this codebase. Can you help me with:

1. **Error Analysis**: What types of errors or issues should I be watching for?
2. **Debugging Strategy**: How should I approach finding and fixing problems?
3. **Prevention**: What practices can help prevent common issues?
4. **Code Review**: What should I focus on when reviewing this code?

Please provide insights on identifying and resolving issues effectively."""
            
            else:
                context += f"**Question:** {question}\n\n"
                context += "Please provide your analysis, insights, and recommendations. I'm looking for your expertise and guidance on this."
        else:
            context += """Please analyze this code and provide your insights on:

1. **Code Quality**: Overall assessment and potential improvements
2. **Best Practices**: Adherence to coding standards and patterns  
3. **Potential Issues**: Any problems or concerns you notice
4. **Recommendations**: Specific suggestions for enhancement
5. **Architecture**: Thoughts on the structure and design

I value your expertise and detailed analysis."""
        
        return context
    
    def _build_incident_solution_prompt(
        self,
        repository_name: str,
        incident_description: str,
        error_logs: Optional[str],
        recent_changes: Optional[str]
    ) -> str:
        """Build prompt for incident solution"""
        
        prompt = f"""Repository: {repository_name}

**Incident Description:**
{incident_description}
"""
        
        if error_logs:
            prompt += f"\n**Error Logs:**\n```\n{error_logs}\n```\n"
        
        if recent_changes:
            prompt += f"\n**Recent Changes:**\n{recent_changes}\n"
        
        prompt += """
Please provide:
1. Root cause analysis
2. Immediate mitigation steps
3. Long-term solution
4. Prevention recommendations
"""
        
        return prompt
    
    def _build_security_review_prompt(
        self,
        repository_name: str,
        code_snippet: Optional[str]
    ) -> str:
        """Build prompt for security review"""
        
        prompt = f"Repository: {repository_name}\n\n"
        
        if code_snippet:
            prompt += f"Code to review:\n```\n{code_snippet}\n```\n\n"
        
        prompt += """Please review for security vulnerabilities including:
- SQL injection
- XSS vulnerabilities
- Authentication/authorization issues
- Sensitive data exposure
- Insecure dependencies
- CSRF vulnerabilities
- Input validation issues

Provide specific recommendations for each finding."""
        
        return prompt
    
    # CLI Command Handlers
    
    async def _execute_command(self, match: re.Match, repository_name: str) -> str:
        """Execute a shell command and return the output"""
        command = match.group(1).strip()
        
        # Security: Only allow safe commands
        safe_commands = ['npm', 'python', 'pytest', 'eslint', 'tsc', 'git', 'ls', 'dir', 'cat', 'type']
        command_parts = command.split()
        
        if not command_parts or command_parts[0] not in safe_commands:
            return f"❌ **Command Not Allowed**\n\nFor security reasons, only these commands are allowed:\n{', '.join(safe_commands)}\n\nTry: `/test` or `/lint` instead."
        
        try:
            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                process.kill()
                return "❌ **Command Timeout**\n\nThe command took too long to execute (>30s)."
            
            output = stdout.decode('utf-8', errors='ignore')
            error = stderr.decode('utf-8', errors='ignore')
            
            result = f"✅ **Command Executed**: `{command}`\n\n"
            
            if output:
                result += f"**Output:**\n```\n{output[:2000]}\n```\n\n"
            
            if error:
                result += f"**Errors:**\n```\n{error[:2000]}\n```\n\n"
            
            if process.returncode != 0:
                result += f"⚠️ Exit code: {process.returncode}"
            
            return result
            
        except Exception as e:
            return f"❌ **Execution Error**\n\n```\n{str(e)}\n```"
    
    async def _run_tests(self, match: re.Match, repository_name: str) -> str:
        """Provide testing insights and guidance"""
        test_path = match.group(1).strip() or "the entire project"
        
        # First, provide intelligent analysis
        analysis = f"""## 🧪 Testing Analysis for {repository_name}

I'd love to help you with testing! Let me share some insights about testing strategies for your project.

### Testing Approach Recommendations

**For Frontend (React/TypeScript):**
- **Unit Tests**: Test individual components with React Testing Library
- **Integration Tests**: Test component interactions and API calls
- **E2E Tests**: Test complete user workflows with Playwright or Cypress
- **Accessibility Tests**: Ensure components work with screen readers

**For Backend (Python/FastAPI):**
- **Unit Tests**: Test individual functions and classes with pytest
- **API Tests**: Test endpoints with TestClient
- **Integration Tests**: Test database operations and external services
- **Performance Tests**: Test response times and load handling

### Key Areas to Focus On

1. **Critical User Paths**: Authentication, data submission, error handling
2. **Edge Cases**: Empty states, error conditions, boundary values
3. **Security**: Input validation, authentication, authorization
4. **Performance**: Response times, memory usage, concurrent requests

### Testing Best Practices

- **Test Behavior, Not Implementation**: Focus on what the code does, not how
- **Use Descriptive Test Names**: Make it clear what each test validates
- **Keep Tests Independent**: Each test should run in isolation
- **Mock External Dependencies**: Don't rely on external APIs or services
- **Maintain Test Data**: Use factories or fixtures for consistent test data

### Common Testing Challenges

- **Async Operations**: Use proper async/await patterns in tests
- **State Management**: Reset state between tests to avoid conflicts
- **External APIs**: Mock HTTP calls to avoid network dependencies
- **Database Tests**: Use test databases or transactions for isolation

"""

        # Try to provide specific insights based on the project structure
        try:
            # Check if we can provide more specific guidance
            if "frontend" in test_path.lower() or "react" in test_path.lower():
                analysis += """
### Frontend Testing Specifics

**Component Testing:**
```typescript
// Test user interactions, not implementation details
test('submits form when button is clicked', () => {
  render(<MyForm />)
  fireEvent.click(screen.getByRole('button', { name: /submit/i }))
  expect(mockSubmit).toHaveBeenCalled()
})
```

**API Testing:**
```typescript
// Mock API calls for predictable tests
vi.mock('../lib/api', () => ({
  api: { getData: vi.fn() }
}))
```
"""
            
            elif "backend" in test_path.lower() or "api" in test_path.lower():
                analysis += """
### Backend Testing Specifics

**API Endpoint Testing:**
```python
def test_create_user(client):
    response = client.post("/users", json={"name": "Test User"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test User"
```

**Database Testing:**
```python
def test_user_creation(db_session):
    user = User(name="Test User")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
```
"""

            # Now try to actually run tests if possible (but don't fail if not available)
            analysis += "\n### 🔍 Attempting to Run Tests...\n\n"
            
            # Try different test runners
            test_commands = [
                ("npm test", "npm"),
                ("pytest", "pytest"),
                ("python -m pytest", "pytest"),
                ("npm run test", "npm"),
            ]
            
            for command, runner in test_commands:
                try:
                    process = await asyncio.create_subprocess_shell(
                        f"{command} {test_path}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        shell=True
                    )
                    
                    try:
                        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        continue
                    
                    output = stdout.decode('utf-8', errors='ignore')
                    error = stderr.decode('utf-8', errors='ignore')
                    
                    if process.returncode == 0 and (output or not error):
                        analysis += f"**✅ Tests executed successfully with {runner}:**\n\n"
                        if output:
                            analysis += f"```\n{output[:800]}\n```\n\n"
                        analysis += "Great! Your tests are passing. Consider adding more tests for edge cases and error conditions.\n"
                        return analysis
                    elif output or error:
                        analysis += f"**⚠️ Test results from {runner}:**\n\n"
                        if output:
                            analysis += f"```\n{output[:800]}\n```\n\n"
                        if error and process.returncode != 0:
                            analysis += f"**Issues found:**\n```\n{error[:800]}\n```\n\n"
                        analysis += "I found some test issues. Would you like help debugging these failures?\n"
                        return analysis
                        
                except Exception:
                    continue
            
            # If no test runner worked, provide guidance
            analysis += """**💡 No test runner detected yet - here's how to get started:**

**For Frontend:**
```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
npm run test
```

**For Backend:**
```bash
pip install pytest pytest-asyncio
pytest
```

**Next Steps:**
1. Set up your testing framework
2. Write tests for critical functionality first
3. Aim for good coverage of happy paths and error cases
4. Run tests regularly during development

Would you like help setting up tests for any specific part of your application?"""
            
            return analysis
            
        except Exception as e:
            return analysis + f"\n\n*Note: Encountered an issue while analyzing: {str(e)}*\n\nBut the testing guidance above should help you get started! What specific testing challenges are you facing?"
    
    async def _run_linter(self, match: re.Match, repository_name: str) -> str:
        """Run linter and return results"""
        lint_path = match.group(1).strip() or "."
        
        result = f"🔍 **Running Linter**\n\nRepository: {repository_name}\nPath: {lint_path}\n\n"
        
        # Try different linters
        lint_commands = [
            ("eslint", "ESLint"),
            ("npm run lint", "npm lint"),
            ("pylint", "Pylint"),
            ("flake8", "Flake8"),
        ]
        
        for command, linter in lint_commands:
            try:
                process = await asyncio.create_subprocess_shell(
                    f"{command} {lint_path}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                except asyncio.TimeoutError:
                    process.kill()
                    continue
                
                output = stdout.decode('utf-8', errors='ignore')
                error = stderr.decode('utf-8', errors='ignore')
                
                if output or error:
                    result += f"**Linter**: {linter}\n\n"
                    
                    combined = output + error
                    if combined:
                        result += f"**Issues Found:**\n```\n{combined[:1500]}\n```\n\n"
                    
                    if process.returncode == 0:
                        result += "✅ **No linting errors!**"
                    else:
                        result += f"⚠️ **Linting issues found** (exit code: {process.returncode})"
                    
                    return result
                    
            except Exception:
                continue
        
        return result + "❌ **No linter found**\n\nTry installing: `npm install eslint` or `pip install pylint`"
    
    async def _find_errors(self, match: re.Match, repository_name: str) -> str:
        """Find errors in code using TypeScript compiler or Python"""
        error_path = match.group(1).strip() or "."
        
        result = f"🐛 **Finding Errors**\n\nRepository: {repository_name}\nPath: {error_path}\n\n"
        
        # Try TypeScript compiler
        try:
            process = await asyncio.create_subprocess_shell(
                f"tsc --noEmit {error_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                process.kill()
                return result + "❌ **Timeout** - Error checking took too long"
            
            output = stdout.decode('utf-8', errors='ignore')
            error = stderr.decode('utf-8', errors='ignore')
            
            combined = output + error
            
            if combined:
                result += f"**TypeScript Errors:**\n```\n{combined[:1500]}\n```\n\n"
                
                if process.returncode == 0:
                    result += "✅ **No TypeScript errors found!**"
                else:
                    result += f"❌ **Found {combined.count('error')} error(s)**"
                
                return result
                
        except Exception:
            pass
        
        # Try Python syntax check
        try:
            process = await asyncio.create_subprocess_shell(
                f"python -m py_compile {error_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
            error = stderr.decode('utf-8', errors='ignore')
            
            if error:
                result += f"**Python Errors:**\n```\n{error[:1500]}\n```\n\n"
                result += "❌ **Syntax errors found**"
                return result
            else:
                result += "✅ **No Python syntax errors found!**"
                return result
                
        except Exception:
            pass
        
        return result + "❌ **No error checker found**\n\nTry: `npm install typescript` or ensure Python is installed"
    
    async def _run_build(self, match: re.Match, repository_name: str) -> str:
        """Run build command"""
        build_target = match.group(1).strip() or ""
        
        result = f"🔨 **Running Build**\n\nRepository: {repository_name}\n\n"
        
        # Try different build commands
        build_commands = [
            f"npm run build {build_target}",
            f"python setup.py build {build_target}",
            f"make {build_target}",
        ]
        
        for command in build_commands:
            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
                except asyncio.TimeoutError:
                    process.kill()
                    return result + "❌ **Build Timeout** - Build took too long (>2min)"
                
                output = stdout.decode('utf-8', errors='ignore')
                error = stderr.decode('utf-8', errors='ignore')
                
                if output or error:
                    result += f"**Command**: `{command}`\n\n"
                    
                    if output:
                        result += f"**Output:**\n```\n{output[-1000:]}\n```\n\n"
                    
                    if error and process.returncode != 0:
                        result += f"**Errors:**\n```\n{error[-1000:]}\n```\n\n"
                    
                    if process.returncode == 0:
                        result += "✅ **Build successful!**"
                    else:
                        result += f"❌ **Build failed** (exit code: {process.returncode})"
                    
                    return result
                    
            except Exception:
                continue
        
        return result + "❌ **No build command found**\n\nTry: `npm install` or configure build scripts"
    
    async def _show_help(self, match: re.Match, repository_name: str) -> str:
        """Show available CLI commands"""
        return """Hey there! 👋 I'm your CloudHelm Assistant, powered by Mistral AI. Think of me as your coding companion who can help you understand, analyze, and improve your code.

## What I Can Do

**💬 Conversational Analysis**
I'm here to chat about your code! Ask me things like:
- "How can I improve the testing in this project?"
- "What are the potential security issues here?"
- "Help me understand this code structure"
- "What's the best way to handle errors in this function?"

**🔧 Code Insights**
I can provide deep analysis on:
- Code quality and best practices
- Architecture and design patterns  
- Performance optimization opportunities
- Security vulnerabilities and fixes
- Testing strategies and approaches

**⚡ Quick Commands** (when you need them)
- `/test` - Get testing insights and run tests
- `/lint` - Code quality analysis and linting
- `/errors` - Help identify and fix issues
- `/build` - Build guidance and execution
- `/run <command>` - Execute safe commands with context
- `/task <description>` - Delegate work to specialized subagents
- `/agents` - List available subagents and their capabilities
- `/status [task_id]` - Check task status or list all tasks

## How I Work

I'm designed to be **conversational and educational**. Instead of just running commands, I'll:
- Explain what I'm analyzing and why
- Provide context and best practices
- Suggest improvements and alternatives
- Help you understand the bigger picture
- Offer insights from my training on millions of codebases

## Examples

Try asking me:
```
"What testing strategy would work best for this React app?"
"Can you review this function for potential issues?"
"How should I structure error handling in this API?"
"What are the security considerations for this authentication code?"
```

I'm here to help you write better code and understand your projects more deeply. What would you like to explore together? 🚀"""
    
    async def _delegate_task(self, match: re.Match, repository_name: str) -> str:
        """Delegate task to specialized subagent"""
        task_description = match.group(1).strip()
        
        # Parse task description to determine agent type
        task_lower = task_description.lower()
        
        if any(word in task_lower for word in ['explore', 'analyze', 'structure', 'understand', 'map']):
            agent_type = 'explore'
        elif any(word in task_lower for word in ['refactor', 'improve', 'optimize', 'clean']):
            agent_type = 'refactor'
        elif any(word in task_lower for word in ['test', 'testing', 'coverage']):
            agent_type = 'test'
        elif any(word in task_lower for word in ['security', 'vulnerability', 'secure']):
            agent_type = 'security'
        elif any(word in task_lower for word in ['performance', 'speed', 'optimize']):
            agent_type = 'performance'
        elif any(word in task_lower for word in ['document', 'docs', 'documentation']):
            agent_type = 'documentation'
        else:
            agent_type = 'explore'  # Default to exploration
        
        return await self.delegate_task(task_description, agent_type, repository_name)
    
    async def _list_agents(self, match: re.Match, repository_name: str) -> str:
        """List available subagents"""
        try:
            from .subagent_service import subagent_service
            agents = subagent_service.get_available_agents()
            
            result = "🤖 **Available Subagents**\n\n"
            result += "I can delegate tasks to specialized subagents for parallel work:\n\n"
            
            for agent_type, config in agents.items():
                auto_approve = "✅ Auto-approved" if config["auto_approve"] else "⚠️ Requires approval"
                result += f"**{config['name']}** (`{agent_type}`)\n"
                result += f"- {config['description']}\n"
                result += f"- Capabilities: {', '.join(config['capabilities'])}\n"
                result += f"- {auto_approve}\n\n"
            
            result += "**Usage:** `/task <description>` - I'll automatically choose the best agent\n"
            result += "**Example:** `/task analyze the authentication flow in this codebase`"
            
            return result
            
        except Exception as e:
            return f"❌ Error listing agents: {str(e)}"
    
    async def _check_task_status(self, match: re.Match, repository_name: str) -> str:
        """Check status of delegated tasks"""
        task_id = match.group(1).strip() if match.group(1) else None
        
        try:
            from .subagent_service import subagent_service
            
            if task_id:
                # Check specific task
                status = subagent_service.get_task_status(task_id)
                if "error" in status:
                    return f"❌ **Task Not Found**: {task_id}"
                
                result = f"📋 **Task Status: {task_id}**\n\n"
                result += f"**Description:** {status['description']}\n"
                result += f"**Agent:** {status['agent_type']}\n"
                result += f"**Status:** {status['status']}\n"
                result += f"**Repository:** {status['repository']}\n"
                
                if status['result']:
                    result += f"\n**Result:**\n{status['result'][:1000]}..."
                elif status['error']:
                    result += f"\n**Error:** {status['error']}"
                
                return result
            else:
                # List all active tasks
                active_tasks = subagent_service.list_active_tasks()
                completed_tasks = subagent_service.list_completed_tasks(5)
                
                result = "📋 **Task Status Overview**\n\n"
                
                if active_tasks:
                    result += f"**Active Tasks ({len(active_tasks)}):**\n"
                    for task in active_tasks:
                        result += f"- `{task['task_id']}` - {task['agent_type']} - {task['status']}\n"
                    result += "\n"
                
                if completed_tasks:
                    result += f"**Recent Completed Tasks ({len(completed_tasks)}):**\n"
                    for task in completed_tasks:
                        status_icon = "✅" if task['status'] == 'completed' else "❌"
                        result += f"- {status_icon} `{task['task_id']}` - {task['agent_type']}\n"
                
                if not active_tasks and not completed_tasks:
                    result += "No tasks found. Use `/task <description>` to delegate work to subagents."
                
                return result
                
        except Exception as e:
            return f"❌ Error checking task status: {str(e)}"


# Global instance
mistral_service = MistralService()
