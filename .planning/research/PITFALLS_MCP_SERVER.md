# Pitfalls Research: MCP Server for wxcode Knowledge Base

**Domain:** MCP Server integration with existing FastAPI/Beanie/Neo4j system
**Researched:** 2026-01-21
**Overall Confidence:** HIGH (verified via official docs, GitHub issues, multiple sources)

---

## Critical Pitfalls

Mistakes that cause rewrites or major system breakage.

### Pitfall 1: Lifespan Conflict - Database Connection Lost

**What goes wrong:** MCP Server mounted into FastAPI replaces the app's lifespan, causing Beanie/MongoDB initialization to never run. All database operations fail with "Beanie not initialized" errors.

**Why it happens:** FastMCP's `http_app()` returns a Starlette app with its own lifespan for session management. If you simply replace FastAPI's lifespan with MCP's lifespan, the existing Beanie initialization is lost.

**Current wxcode code at risk:**
```python
# src/wxcode/main.py lines 25-35
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = await init_db()  # THIS MUST STILL RUN
    app.state.db_client = client
    yield
    await close_db(client)
```

**Consequences:**
- All MCP tools that query MongoDB will fail
- Neo4j sync will fail
- Silent failures if not caught (tools return empty results)

**Prevention:**
1. Use `combine_lifespans()` from fastmcp utilities:
   ```python
   from fastmcp.utilities.lifespan import combine_lifespans

   mcp_app = mcp.http_app(path="/mcp")
   app = FastAPI(lifespan=combine_lifespans(lifespan, mcp_app.lifespan))
   ```
2. Test MCP tools actually connect to database before deployment

**Detection:**
- MCP tools return empty arrays when data exists
- Errors mentioning "collection not initialized" or "Beanie"
- First database operation after MCP call fails

**Phase to address:** Phase 1 (Infrastructure setup)

**Sources:**
- [FastMCP Lifespan Issue #580](https://github.com/jlowin/fastmcp/issues/580)
- [FastMCP Lifespan Discussion #1763](https://github.com/jlowin/fastmcp/discussions/1763)

---

### Pitfall 2: STDIO Transport Logging Corruption

**What goes wrong:** MCP server using STDIO transport crashes or produces garbled responses because logging writes to stdout, corrupting JSON-RPC messages.

**Why it happens:** Python's default `print()` and `logging.basicConfig()` write to stdout. STDIO transport uses stdout for JSON-RPC communication. Any non-JSON output corrupts the protocol.

**Current wxcode code at risk:**
- Debug print statements in parsers
- logging configured without explicit stderr handler
- Third-party libraries that print to stdout

**Consequences:**
- MCP client receives malformed JSON
- Connection drops silently
- Intermittent failures hard to reproduce

**Prevention:**
1. Configure logging to ONLY write to stderr:
   ```python
   logging.basicConfig(
       level=logging.INFO,
       stream=sys.stderr,  # CRITICAL: not stdout
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```
2. Never use `print()` in MCP server code
3. Use HTTP/SSE transport for development (easier debugging)

**Detection:**
- MCP Inspector shows "invalid JSON" errors
- Connections work sometimes but not others
- Log messages appearing in MCP response

**Phase to address:** Phase 1 (Infrastructure setup)

**Sources:**
- [Stainless MCP Error Handling Guide](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers)
- [MCP Server Debugging Guide](https://mcpcat.io/guides/error-handling-custom-mcp-servers/)

---

### Pitfall 3: Token Explosion from Tool Definitions

**What goes wrong:** MCP server with 20+ tools consumes 30,000+ tokens just from tool definitions, leaving minimal context for actual work. Claude Code becomes sluggish or hits context limits.

**Why it happens:** Each MCP tool includes: name, description, parameter schema, examples. wxcode's KB has many query dimensions (elements, controls, dependencies, schema, procedures). Natural tendency is to create a tool for each query type.

**wxcode specific risk:**
- Element queries (by type, by layer, by status, by project)
- Control queries (by element, by type, with events, with binding)
- Dependency queries (uses, used_by, impact analysis)
- Schema queries (tables, relationships, fields)
- Graph queries (paths, hubs, dead code)

**If each becomes a separate tool:** 15+ tools x 500-2000 tokens each = 7,500-30,000 tokens before conversation starts.

**Consequences:**
- 15-30% of context window consumed by tool definitions
- Slower response times
- Cursor has 40-tool hard limit (would be approached)

**Prevention:**
1. **Consolidate tools by domain:**
   - `search_elements` (with filters) instead of 5 separate element tools
   - `query_graph` (with operation type) instead of 4 graph tools
2. **Use terse descriptions:** 1-2 sentences max, no examples in description
3. **Defer tool loading:** Use semantic tool search or dynamic toolsets
4. **Track token usage:** Monitor tool definition size

**Detection:**
- MCP Inspector shows large tool payload
- Claude Code feels slower after MCP enabled
- Token usage metrics spike on initialization

**Phase to address:** Phase 2 (Tool design)

**Sources:**
- [Speakeasy: Reducing MCP Token Usage by 100x](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2)
- [MCP Token Bloat SEP-1576](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1576)
- [Scott Spence: Optimizing MCP Context](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)

---

### Pitfall 4: Async Deadlocks in Tool Handlers

**What goes wrong:** MCP tool calls hang indefinitely because async operations block each other or await operations that never complete.

**Why it happens:**
- Calling sync code from async context without `run_in_executor`
- Nested async calls that create implicit dependencies
- Using blocking I/O (file reads) without async variants

**wxcode specific risk:**
```python
# Bad: Sync Neo4j call in async handler
def get_impact_sync(element_name):  # SYNC!
    with driver.session() as session:
        return session.run(query)

@mcp.tool
async def impact_analysis(element: str):
    return get_impact_sync(element)  # BLOCKS EVENT LOOP
```

**Consequences:**
- Tool calls never return
- Server appears hung
- No error message (just timeout)

**Prevention:**
1. **Use async throughout:** Beanie is already async, Neo4j has async driver
2. **Wrap sync code:** If unavoidable, use `asyncio.to_thread()` or `run_in_executor`
3. **Set timeouts:** Always wrap long operations:
   ```python
   async with asyncio.timeout(30):
       result = await long_operation()
   ```
4. **Test with MCP Inspector:** Verify tools return in reasonable time

**Detection:**
- Tool calls don't return
- Server CPU low but call pending
- Works with small data, hangs with large data

**Phase to address:** Phase 2 (Tool implementation)

**Sources:**
- [MCP Request Timeout Guide](https://mcpcat.io/guides/fixing-mcp-error-32001-request-timeout/)
- [GitHub Issue: Session.call_tool stuck](https://github.com/modelcontextprotocol/python-sdk/issues/262)

---

## Common Mistakes

Frequently made errors that cause delays or technical debt.

### Mistake 1: Returning Full Documents Instead of Summaries

**What goes wrong:** MCP tool returns entire Element or Control documents (including raw_content, AST, all properties) when only summary needed. Response exceeds context limits or overwhelms LLM.

**Why it happens:** Easy to `return element.model_dump()` and call it done. Feels complete but transfers too much data.

**wxcode specific risk:**
- Element.raw_content can be 10,000+ characters
- Element.ast contains full parsed procedures/events
- Control.events contains full WLanguage code
- Returning 50 elements = potentially 500KB+ JSON

**Prevention:**
1. **Create response models:** Define what each tool returns explicitly
   ```python
   class ElementSummary(BaseModel):
       id: str
       name: str
       type: ElementType
       conversion_status: ConversionStatus
       dependencies_count: int  # Not full dependency list
   ```
2. **Paginate large results:** Max 20-50 items per response
3. **Offer detail endpoints:** `get_element_detail(id)` for full data

**Detection:**
- MCP responses over 50KB
- Claude Code says "response too long"
- Tool works for 1 item but fails for list

**Phase to address:** Phase 2 (Tool design)

---

### Mistake 2: Missing Pagination for Large Collections

**What goes wrong:** Tool queries all elements/controls without limit, causing memory exhaustion or timeout.

**Why it happens:** Works fine in development with 100 elements. Production project has 5,000 elements.

**wxcode specific numbers (Linkpay_ADM reference project):**
- 500+ Elements
- 2,000+ Controls
- 1,000+ Dependencies

**Prevention:**
1. **Always default to pagination:**
   ```python
   @mcp.tool
   async def list_elements(
       project: str,
       limit: int = 20,  # Default limit
       offset: int = 0,
       filters: Optional[dict] = None
   ):
       return await Element.find(query).skip(offset).limit(limit).to_list()
   ```
2. **Return pagination metadata:**
   ```python
   return {
       "items": results,
       "total": total_count,
       "limit": limit,
       "offset": offset,
       "has_more": offset + len(results) < total_count
   }
   ```
3. **Document limits in tool description**

**Detection:**
- Memory spikes during tool calls
- Tools work for small projects, timeout for large ones
- LLM struggles to process all items

**Phase to address:** Phase 2 (Tool implementation)

**Sources:**
- [MCP Pagination Specification](https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/pagination)

---

### Mistake 3: No Input Validation on Resource Templates

**What goes wrong:** Resource URI template like `element://{project}/{element_name}` accepts arbitrary input, allowing path traversal or injection attacks.

**Why it happens:** Trust that LLM will send valid parameters. Forget that MCP is an attack surface.

**Security implications:**
- Project/element names could contain `../` or special characters
- Cypher/MongoDB queries could be injected through names
- Even with LLM filter, prompt injection could trigger malicious calls

**Prevention:**
1. **Validate all inputs:**
   ```python
   def validate_element_name(name: str) -> str:
       if not re.match(r'^[A-Z][A-Za-z0-9_]*$', name):
           raise ValueError(f"Invalid element name: {name}")
       return name
   ```
2. **Use allowlists:** For project names, query from database
3. **Parameterize queries:** Never interpolate user input into Cypher/MongoDB queries
4. **Treat resource URIs as untrusted input**

**Detection:**
- Security scanner finds injection vulnerabilities
- Unexpected query results
- Errors with special characters in names

**Phase to address:** Phase 2 (Tool implementation)

**Sources:**
- [MCP Security Best Practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices)
- [mcp-scanner Tool](https://www.darknet.org.uk/2025/10/mcp-scanner-python-mcp-scanner-for-prompt-injection-and-insecure-agents/)

---

### Mistake 4: Ignoring Neo4j Connection Pool Exhaustion

**What goes wrong:** Neo4j driver runs out of connections because MCP tools don't properly release sessions.

**Why it happens:** Each tool call creates new session, concurrent calls from Claude Code exhaust pool.

**wxcode specific context:**
- Impact analysis uses multiple Neo4j queries
- Graph traversal holds connection while iterating
- Many concurrent tool calls during exploration

**Prevention:**
1. **Use async with for all sessions:**
   ```python
   async with driver.session() as session:
       result = await session.run(query)
       return [record async for record in result]
   ```
2. **Configure pool size:** Match expected concurrency
3. **Add connection health checks:** Verify before complex operations
4. **Use read transactions for queries:**
   ```python
   async def query():
       async with driver.session() as session:
           return await session.execute_read(tx_function)
   ```

**Detection:**
- "Connection pool exhausted" errors
- Tools work individually but fail under load
- Neo4j shows many idle connections

**Phase to address:** Phase 3 (Integration testing)

---

### Mistake 5: Not Handling Tool Errors Gracefully

**What goes wrong:** Tool raises exception, MCP server crashes or returns cryptic error, Claude Code has no idea what went wrong.

**Why it happens:** No try/catch in tool handlers. Beanie/Neo4j errors bubble up raw.

**Consequences:**
- Claude Code retries the same broken call
- User has no actionable information
- Server may need restart

**Prevention:**
1. **Wrap all tools in error handler:**
   ```python
   @mcp.tool
   async def search_elements(project: str, query: str):
       try:
           return await _search_elements(project, query)
       except DocumentNotFound:
           return {"error": f"Project '{project}' not found", "code": "PROJECT_NOT_FOUND"}
       except Exception as e:
           logger.exception("search_elements failed")
           return {"error": str(e), "code": "INTERNAL_ERROR"}
   ```
2. **Use structured error responses:** Include error code and message
3. **Log errors with context:** Include parameters that caused failure

**Detection:**
- Tools return Python exception traces
- MCP Inspector shows raw errors
- Claude Code says "tool failed" without explanation

**Phase to address:** Phase 2 (Tool implementation)

**Sources:**
- [FastMCP Error Handling Middleware](https://gofastmcp.com/python-sdk/fastmcp-server-middleware-error_handling)

---

## Integration Pitfalls

Specific to adding MCP to existing wxcode system.

### Integration Pitfall 1: Beanie Document Serialization Issues

**What goes wrong:** MCP tool returns Beanie Document, but ObjectId and Link fields aren't JSON serializable.

**Why it happens:** Beanie Documents use `PydanticObjectId` and `Link[T]` types. These don't serialize to JSON without custom handling.

**wxcode specific:**
```python
# Element model has these problematic fields:
project_id: Link[Project]  # Not JSON serializable
# Control model:
element_id: PydanticObjectId
type_definition_id: Optional[PydanticObjectId]
```

**Prevention:**
1. **Create serializable response models:**
   ```python
   class ElementResponse(BaseModel):
       id: str  # str(element.id)
       project_id: str  # str(element.project_id.ref.id)
       # ... other fields
   ```
2. **Use Pydantic's json serialization:**
   ```python
   return element.model_dump(mode='json')  # Handles ObjectId
   ```
3. **Exclude Link fields or resolve them:**
   ```python
   return element.model_dump(exclude={'project_id'}, mode='json')
   ```

**Detection:**
- "Object of type ObjectId is not JSON serializable"
- MCP tools crash on return
- Partial data in responses

**Phase to address:** Phase 2 (Tool implementation)

---

### Integration Pitfall 2: Existing API Routes Conflict with MCP Mount

**What goes wrong:** MCP server mounted at path that conflicts with existing routes, causing 404s or routing confusion.

**wxcode existing routes:**
- `/api/projects/*`
- `/api/elements/*`
- `/api/conversions/*`
- `/api/tree/*`

**If MCP mounted at `/api/`:** Would shadow all existing routes.

**Prevention:**
1. **Use dedicated MCP path:** `/mcp` or `/.mcp`
2. **Mount MCP app explicitly:**
   ```python
   mcp_app = mcp.http_app(path="/mcp")
   app.mount("/mcp", mcp_app)
   ```
3. **Test existing routes still work after MCP integration**

**Detection:**
- Existing API calls return 404 or unexpected responses
- MCP and API responses interleaved
- Route conflicts in FastAPI docs

**Phase to address:** Phase 1 (Infrastructure setup)

---

### Integration Pitfall 3: State Mutation Tools Without Confirmation

**What goes wrong:** MCP tool that marks elements as converted runs without user confirmation, accidentally modifying production data.

**Why it happens:** Natural to expose write operations as tools. LLM calls them thinking they're safe.

**wxcode specific:**
- `mark_converted(element_id)` - Changes conversion.status
- `update_dependencies(element_id)` - Modifies dependency graph
- `set_topological_order(project_id)` - Changes all element orders

**Security implications:**
- Prompt injection could trigger unintended writes
- LLM might "helpfully" mark things converted that aren't
- No audit trail of who/why changed status

**Prevention:**
1. **Separate read and write tools clearly:**
   ```python
   # Read tools (safe)
   @mcp.tool
   async def get_element(id: str): ...

   # Write tools (dangerous - require confirmation)
   @mcp.tool
   async def mark_element_converted(
       id: str,
       confirmation: str  # Must be "I confirm converting {element_name}"
   ): ...
   ```
2. **Use resource URIs for reads, tools for writes**
3. **Add audit logging for all mutations**
4. **Consider read-only mode by default**

**Detection:**
- Data changed unexpectedly
- Conversion status wrong
- No record of who made changes

**Phase to address:** Phase 2 (Tool design)

**Sources:**
- [MCP Security: Human in Loop](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices) - "Treat SHOULD as MUST for human confirmation"

---

### Integration Pitfall 4: Long-Running Graph Operations Timeout

**What goes wrong:** Neo4j graph traversal for large dependency analysis exceeds MCP timeout (default 60s in some clients).

**Why it happens:** `impact_analysis(element)` might traverse thousands of nodes. `find_path(a, b)` might explore entire graph.

**wxcode specific:**
- Projects have 500+ elements with complex dependencies
- Some elements are "hub" nodes with 50+ connections
- Full topological sort touches all nodes

**Prevention:**
1. **Set depth limits:**
   ```python
   @mcp.tool
   async def impact_analysis(element: str, max_depth: int = 2):
       # Limit traversal depth
   ```
2. **Stream partial results with progress:**
   ```python
   # Use MCP progress notifications
   await context.report_progress(0.5, "Analyzed 500/1000 dependencies")
   ```
3. **For long operations, return task ID:**
   ```python
   @mcp.tool
   async def full_dependency_analysis(project: str):
       task_id = await start_background_task(project)
       return {"task_id": task_id, "status": "started",
               "poll_with": "get_task_status(task_id)"}
   ```
4. **Cache expensive computations**

**Detection:**
- Graph queries timeout consistently
- Works for small projects, fails for large
- Client receives timeout error

**Phase to address:** Phase 2 (Tool implementation)

**Sources:**
- [MCP Tasks for Long-Running Operations](https://workos.com/blog/mcp-async-tasks-ai-agent-workflows)
- [SEP-1391: Long-Running Operations](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1391)

---

### Integration Pitfall 5: Async Context Loss Between Requests

**What goes wrong:** First MCP request works, subsequent requests fail with "collection not initialized" or similar.

**Why it happens:** Some async contexts (like Beanie's database reference) aren't properly propagated across requests in certain deployment modes.

**wxcode specific context:**
- Using Beanie's Document.find() class methods
- These rely on initialized Beanie context
- STDIO transport creates new context per message

**Prevention:**
1. **Verify Beanie initialization in each handler:**
   ```python
   @mcp.tool
   async def search_elements(project: str):
       # Defensive check
       if not hasattr(Element, '_document_settings'):
           raise RuntimeError("Database not initialized")
       return await Element.find(...).to_list()
   ```
2. **Use dependency injection for database access**
3. **Test multiple sequential tool calls**
4. **Consider HTTP transport for stateful scenarios**

**Detection:**
- First request works, second fails
- "No database configured" errors after successful calls
- Intermittent failures

**Phase to address:** Phase 3 (Integration testing)

**Sources:**
- [GitHub: MCP Connection Invalidation](https://github.com/microsoft/agent-framework/issues/2884)
- [MCP Server Hang Issues](https://github.com/modelcontextprotocol/python-sdk/issues/547)

---

## Prevention Checklist

Quick reference for each phase.

### Phase 1: Infrastructure Setup

- [ ] Use `combine_lifespans()` to merge Beanie and MCP lifespans
- [ ] Configure logging to stderr only (not stdout)
- [ ] Mount MCP at dedicated path (`/mcp`) not overlapping with existing routes
- [ ] Test STDIO and HTTP transports both work
- [ ] Verify Beanie initialization persists across MCP requests

### Phase 2: Tool Design & Implementation

- [ ] Keep total tools under 15 (consolidate by domain)
- [ ] Keep each tool description under 100 words
- [ ] Create response models (don't return raw Documents)
- [ ] Add pagination to all list operations (default limit 20)
- [ ] Validate all string inputs (element names, project names)
- [ ] Wrap all database calls in try/catch with structured errors
- [ ] Use async throughout (no blocking calls)
- [ ] Set timeouts on long operations (30s default)
- [ ] Separate read tools from write tools
- [ ] Require confirmation for state-mutating operations
- [ ] Convert ObjectId/Link fields to strings in responses

### Phase 3: Integration Testing

- [ ] Test tools against production-sized data (500+ elements)
- [ ] Test 10 sequential tool calls (verify no context loss)
- [ ] Test concurrent tool calls (verify no deadlocks)
- [ ] Run mcp-scanner for security vulnerabilities
- [ ] Verify Neo4j connection pool handles load
- [ ] Test with MCP Inspector before Claude Code integration
- [ ] Measure token usage of tool definitions
- [ ] Test existing FastAPI routes still work

### Phase 4: Production Deployment

- [ ] Monitor tool response times
- [ ] Set up error alerting for MCP failures
- [ ] Document tool capabilities for Claude Code users
- [ ] Consider read-only mode for initial deployment
- [ ] Plan rollback if MCP causes issues

---

## Sources Summary

**Official Documentation:**
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Security Best Practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices)
- [MCP Pagination Specification](https://modelcontextprotocol.io/specification/2025-03-26/server/utilities/pagination)

**Best Practices & Guides:**
- [Nearform: MCP Tips, Tricks and Pitfalls](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/)
- [7 Critical MCP Mistakes to Avoid](https://www.geeky-gadgets.com/model-context-protocol-mistakes-to-avoid/)
- [Stainless: MCP Error Handling](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers)
- [MCPcat: Error Handling Guide](https://mcpcat.io/guides/error-handling-custom-mcp-servers/)

**Token Optimization:**
- [Speakeasy: Reducing Token Usage by 100x](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2)
- [Scott Spence: Optimizing MCP Context](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)

**Async & Timeout Issues:**
- [WorkOS: MCP Async Tasks](https://workos.com/blog/mcp-async-tasks-ai-agent-workflows)
- [MCP Request Timeout Guide](https://mcpcat.io/guides/fixing-mcp-error-32001-request-timeout/)
- [SEP-1391: Long-Running Operations](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1391)

**FastMCP Specific:**
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [FastMCP Lifespan Issue #580](https://github.com/jlowin/fastmcp/issues/580)
- [FastMCP Error Handling Middleware](https://gofastmcp.com/python-sdk/fastmcp-server-middleware-error_handling)

**Security:**
- [Snyk Labs: Prompt Injection Meets MCP](https://labs.snyk.io/resources/prompt-injection-mcp/)
- [MCP Scanner Tool](https://www.darknet.org.uk/2025/10/mcp-scanner-python-mcp-scanner-for-prompt-injection-and-insecure-agents/)

**Neo4j MCP:**
- [Neo4j MCP Integration Guide](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/)
- [Official Neo4j MCP Server](https://github.com/neo4j/mcp)
