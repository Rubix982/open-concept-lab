class PersistentKVCache:
    """
    Version-controlled transformer KV cache
    Enables branching conversations without recomputation
    """
    
    def __init__(self, num_layers, num_heads, head_dim):
        self.num_layers = num_layers
        self.cache_tree = {}  # version_id -> cache_node
        self.current_version = 0
        
    def fork(self):
        """
        Create new version (path copying from current)
        O(1) operation due to structural sharing
        """
        new_version = self.current_version + 1
        
        # Share all old KV pairs, prepare for new additions
        self.cache_tree[new_version] = CacheNode(
            parent=self.current_version,
            shared_keys=self.cache_tree[self.current_version].keys,
            shared_values=self.cache_tree[self.current_version].values,
            new_keys=[],  # Will accumulate new tokens
            new_values=[]
        )
        
        self.current_version = new_version
        return new_version
    
    def get_kv_at_layer(self, layer_idx, version=None):
        """
        Retrieve KV cache for specific layer and version
        """
        if version is None:
            version = self.current_version
        
        node = self.cache_tree[version]
        
        # Accumulate KVs from current node and ancestors
        keys, values = [], []
        while node is not None:
            keys = node.new_keys[layer_idx] + keys
            values = node.new_values[layer_idx] + values
            node = self.cache_tree.get(node.parent)
        
        return torch.cat(keys), torch.cat(values)