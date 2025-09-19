import warnings, copy, time, uuid, json
from datetime import datetime
from typing import Dict, Any, List, Optional

# ======================================================================
# CORE CLASSES
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
    def exec(self, prep_res): pass
    def post(self, shared, prep_res, exec_res): pass

    def before_run(self, shared): pass
    def after_run(self, shared): pass

    def on_error(self, exc, shared):
        """Hook called when an error occurs"""
        raise exc
    
    def _exec(self, prep_res):
        try:
            return self.exec(prep_res)
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
            try: return self.exec(prep_res)
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
# PUBLIC API
# ======================================================================

__all__ = ['BaseNode', 'Node', 'BatchNode', 'Flow']
