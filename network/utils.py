from collections import deque
from .models import Edge


def find_path(start_node, end_node):
    if start_node.id == end_node.id:
        return [start_node]
    visited = {start_node.id}
    queue = deque([[start_node]])
    while queue:
        path = queue.popleft()
        current = path[-1]
        for edge in Edge.objects.filter(from_node=current).select_related('to_node'):
            neighbor = edge.to_node
            if neighbor.id not in visited:
                new_path = path + [neighbor]
                if neighbor.id == end_node.id:
                    return new_path
                visited.add(neighbor.id)
                queue.append(new_path)
    return None


def get_nodes_within_hops(node_ids, max_hops=2):
    reachable = set(node_ids)
    frontier = set(node_ids)
    for _ in range(max_hops):
        forward = set(Edge.objects.filter(from_node_id__in=frontier).values_list('to_node_id', flat=True))
        backward = set(Edge.objects.filter(to_node_id__in=frontier).values_list('from_node_id', flat=True))
        new_nodes = (forward | backward) - reachable
        reachable |= new_nodes
        frontier = new_nodes
    return reachable
