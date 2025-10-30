import warnings, copy, time, uuid, json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

# ======================================================================
# SYNC CORE CLASSES
# ======================================================================

class BaseNode:
    def __init__(self, name=None):
        self.params, self.successors = {}, {}
        self.name = name or f"{self.__class__.__name__}_{id(self)}"
        self.context = None
    
    def set_params(self, params): 
        self.params = params
    
    def next(self, node, action="default"):
        if action in self.successors: 
            warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action] = node
        return node
    
    def prep(self, shared): pass
    
    def exec(self, prep_res):
        """Override this method in subclasses to implement node logic."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.exec() must be overridden. "
            f"BaseNode.exec() is abstract and cannot be used directly."
        )
    
    def post(self, shared, prep_res, exec_res): pass

    def before_run(self, shared): pass
    def after_run(self, shared): pass

    def on_error(self, exc, shared):
        """Hook called when an error occurs"""
        raise exc
    
    def _exec(self, prep_res):
        try:
            result = self.exec(prep_res)
            # Check if exec() was not overridden (returns None from base implementation)
            # We check if the method is the exact same object as BaseNode.exec
            if result is None and type(self).exec is BaseNode.exec:
                raise NotImplementedError(
                    f"{self.__class__.__name__}.exec() returned None. "
                    f"Did you forget to override exec()? "
                    f"All nodes must implement exec() method."
                )
            return result
        except Exception as e:
            raise
    
    def _run(self, shared):
        self.before_run(shared)
        try:
            p = self.prep(shared)
            e = self._exec(p)
            result = self.post(shared, p, e)
            self.after_run(shared)
            return result
        except Exception as exc:
            return self.on_error(exc, shared)
    
    def run(self, shared, context=None):
        self.context = context
        if self.successors: 
            warnings.warn("Node won't run successors. Use Flow.")
        return self._run(shared)
    
    def __rshift__(self, other): return self.next(other)
    def __sub__(self, action):
        if isinstance(action, str): 
            return _ConditionalTransition(self, action)
        raise TypeError("Action must be a string")


class _ConditionalTransition:
    """Internal helper for conditional transitions (node - 'action' >> next_node)"""
    def __init__(self, src, action): 
        self.src, self.action = src, action
    def __rshift__(self, tgt): return self.src.next(tgt, self.action)


class Node(BaseNode):
    def __init__(self, name=None, max_retries=1, wait=0):
        super().__init__(name)
        self.max_retries, self.wait = max_retries, wait
    
    def exec_fallback(self, prep_res, exc): raise exc
    
    def _exec(self, prep_res):
        for self.cur_retry in range(self.max_retries):
            try: 
                result = self.exec(prep_res)
                # Same check as BaseNode, but after successful execution
                if result is None and type(self).exec is BaseNode.exec:
                    raise NotImplementedError(
                        f"{self.__class__.__name__}.exec() returned None. "
                        f"Did you forget to override exec()? "
                        f"All nodes must implement exec() method."
                    )
                return result
            except Exception as e:
                if self.cur_retry == self.max_retries - 1: 
                    return self.exec_fallback(prep_res, e)
                if self.wait > 0: time.sleep(self.wait)


class BatchNode(Node):
    def _exec(self, items):
        return [super(BatchNode, self)._exec(i) for i in (items or [])]


class Flow(BaseNode):
    def __init__(self, name=None, start=None):
        super().__init__(name)
        self.start_node = start
    
    # Flow doesn't need exec() override check since it uses _orch() instead
    def exec(self, prep_res): 
        pass
    
    def start(self, start): 
        self.start_node = start
        return start
    
    def get_next_node(self, curr, action):
        nxt = curr.successors.get(action or "default")
        if not nxt and curr.successors:
            warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt
    
    def _orch(self, shared, params=None):
        curr, p, last_action = copy.copy(self.start_node), (params or {**self.params}), None
        while curr:
            curr.context = self.context
            curr.set_params(p)
            last_action = curr._run(shared)
            curr = copy.copy(self.get_next_node(curr, last_action))
        return last_action
    
    def _run(self, shared):
        self.before_run(shared)
        try:
            p = self.prep(shared)
            o = self._orch(shared)
            result = self.post(shared, p, o)
            self.after_run(shared)
            return result
        except Exception as exc:
            return self.on_error(exc, shared)
    
    def post(self, shared, prep_res, exec_res): return exec_res
    
    def to_dict(self):
        nodes_seen, nodes, edges = set(), [], []
        def walk(node):
            if id(node) in nodes_seen: return
            nodes_seen.add(id(node))
            nodes.append({"name": node.name,"type": node.__class__.__name__})
            for action, next_node in node.successors.items():
                edges.append({"from": node.name,"to": next_node.name,"action": action})
                walk(next_node)
        if self.start_node: walk(self.start_node)
        return {"nodes": nodes, "edges": edges}
    
    def to_mermaid(self):
        graph = self.to_dict()
        lines = ["graph TD"]
        for edge in graph["edges"]:
            action_label = f"|{edge['action']}|" if edge['action'] != 'default' else ''
            lines.append(f"    {edge['from']} -->{action_label} {edge['to']}")
        return "\n".join(lines)


# ======================================================================
# ASYNC CLASSES
# ======================================================================

class _AsyncConditionalTransition:
    """Helper for async conditional transitions"""
    def __init__(self, src, action):
        self.src, self.action = src, action
    def __rshift__(self, tgt): return self.src.next(tgt, self.action)


class AsyncNode:
    """Async version of Node with full Agora features"""
    
    def __init__(self, name=None, max_retries=1, wait=0):
        self.params, self.successors = {}, {}
        self.name = name or f"{self.__class__.__name__}_{id(self)}"
        self.context = None
        self.max_retries, self.wait = max_retries, wait
    
    def set_params(self, params): self.params = params
    def next(self, node, action="default"):
        if action in self.successors:
            warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action] = node
        return node
    
    # Async methods
    async def prep_async(self, shared): pass
    
    async def exec_async(self, prep_res):
        """Override this method in subclasses to implement async node logic."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.exec_async() must be overridden. "
            f"AsyncNode.exec_async() is abstract and cannot be used directly."
        )
    
    async def post_async(self, shared, prep_res, exec_res): pass
    async def before_run_async(self, shared): pass
    async def after_run_async(self, shared): pass
    async def on_error_async(self, exc, shared): raise exc
    async def exec_fallback_async(self, prep_res, exc): raise exc
    
    async def _exec_async(self, prep_res):
        for self.cur_retry in range(self.max_retries):
            try: 
                result = await self.exec_async(prep_res)
                # Check if exec_async() was not overridden
                if result is None and type(self).exec_async is AsyncNode.exec_async:
                    raise NotImplementedError(
                        f"{self.__class__.__name__}.exec_async() returned None. "
                        f"Did you forget to override exec_async()? "
                        f"All async nodes must implement exec_async() method."
                    )
                return result
            except Exception as e:
                if self.cur_retry == self.max_retries - 1:
                    return await self.exec_fallback_async(prep_res, e)
                if self.wait > 0: await asyncio.sleep(self.wait)
    
    async def _run_async(self, shared):
        await self.before_run_async(shared)
        try:
            p = await self.prep_async(shared)
            e = await self._exec_async(p)
            result = await self.post_async(shared, p, e)
            await self.after_run_async(shared)
            return result
        except Exception as exc:
            return await self.on_error_async(exc, shared)
    
    async def run_async(self, shared, context=None):
        self.context = context
        if self.successors:
            warnings.warn("Node won't run successors. Use AsyncFlow.")
        return await self._run_async(shared)
    
    def __rshift__(self, other): return self.next(other)
    def __sub__(self, action):
        if isinstance(action, str):
            return _AsyncConditionalTransition(self, action)
        raise TypeError("Action must be a string")


class AsyncBatchNode(AsyncNode):
    """Async batch node - sequential processing"""
    async def _exec_async(self, items):
        results = []
        for item in (items or []):
            result = await super(AsyncBatchNode, self)._exec_async(item)
            results.append(result)
        return results


class AsyncParallelBatchNode(AsyncNode):
    """Async parallel batch node - concurrent processing"""
    async def _exec_async(self, items):
        if not items: return []
        
        async def process_item(item):
            for retry in range(self.max_retries):
                try: 
                    result = await self.exec_async(item)
                    # Check for unimplemented exec_async
                    if result is None and type(self).exec_async is AsyncNode.exec_async:
                        raise NotImplementedError(
                            f"{self.__class__.__name__}.exec_async() returned None. "
                            f"Did you forget to override exec_async()?"
                        )
                    return result
                except Exception as e:
                    if retry == self.max_retries - 1:
                        return await self.exec_fallback_async(item, e)
                    if self.wait > 0: await asyncio.sleep(self.wait)
        
        return await asyncio.gather(*[process_item(item) for item in items])


class AsyncFlow:
    """Async version of Flow with full Agora features"""
    
    def __init__(self, name=None, start=None):
        self.params, self.successors = {}, {}
        self.name = name or f"{self.__class__.__name__}_{id(self)}"
        self.context = None
        self.start_node = start
    
    def start(self, start): self.start_node = start; return start
    def set_params(self, params): self.params = params
    
    def get_next_node(self, curr, action):
        nxt = curr.successors.get(action or "default")
        if not nxt and curr.successors:
            warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt
    
    # Async methods
    async def prep_async(self, shared): pass
    async def post_async(self, shared, prep_res, exec_res): return exec_res
    async def before_run_async(self, shared): pass
    async def after_run_async(self, shared): pass
    async def on_error_async(self, exc, shared): raise exc
    
    async def _orch_async(self, shared, params=None):
        curr = copy.copy(self.start_node)
        p = params or {**self.params}
        last_action = None
        while curr:
            curr.context = self.context
            curr.set_params(p)
            last_action = await curr._run_async(shared)
            curr = copy.copy(self.get_next_node(curr, last_action))
        return last_action
    
    async def _run_async(self, shared):
        await self.before_run_async(shared)
        try:
            p = await self.prep_async(shared)
            o = await self._orch_async(shared)
            result = await self.post_async(shared, p, o)
            await self.after_run_async(shared)
            return result
        except Exception as exc:
            return await self.on_error_async(exc, shared)
    
    async def run_async(self, shared, context=None):
        self.context = context
        if self.successors:
            warnings.warn("Node won't run successors. Use AsyncFlow.")
        return await self._run_async(shared)
    
    def to_dict(self):
        nodes_seen, nodes, edges = set(), [], []
        def walk(node):
            if id(node) in nodes_seen: return
            nodes_seen.add(id(node))
            nodes.append({"name": node.name, "type": node.__class__.__name__})
            for action, next_node in node.successors.items():
                edges.append({"from": node.name, "to": next_node.name, "action": action})
                walk(next_node)
        if self.start_node: walk(self.start_node)
        return {"nodes": nodes, "edges": edges}
    
    def to_mermaid(self):
        graph = self.to_dict()
        lines = ["graph TD"]
        for edge in graph["edges"]:
            action_label = f"|{edge['action']}|" if edge['action'] != 'default' else ''
            lines.append(f"    {edge['from']} -->{action_label} {edge['to']}")
        return "\n".join(lines)


class AsyncBatchFlow(AsyncFlow):
    """Async batch flow - sequential sub-flow execution"""
    async def _orch_async(self, shared, params=None):
        items = params or shared.get("items", [])
        results = []
        for item in items:
            item_shared = {"item": item, **shared}
            result = await super()._orch_async(item_shared, params)
            results.append(result)
        shared["batch_results"] = results
        return results


class AsyncParallelBatchFlow(AsyncFlow):
    """Async parallel batch flow - concurrent sub-flow execution"""
    async def _orch_async(self, shared, params=None):
        items = params or shared.get("items", [])
        async def process_item(item):
            item_shared = {"item": item, **shared}
            return await super(AsyncParallelBatchFlow, self)._orch_async(item_shared, params)
        results = await asyncio.gather(*[process_item(item) for item in items])
        shared["batch_results"] = results
        return results


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    # Sync classes
    'BaseNode', 'Node', 'BatchNode', 'Flow',
    # Async classes  
    'AsyncNode', 'AsyncFlow', 'AsyncBatchNode', 'AsyncParallelBatchNode',
    'AsyncBatchFlow', 'AsyncParallelBatchFlow'
]
