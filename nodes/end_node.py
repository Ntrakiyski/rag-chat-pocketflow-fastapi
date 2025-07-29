from pocketflow import Node

class EndNode(Node):
    def exec(self, _):
        print("Flow has reached a terminal state. Shutting down.")
        # This node does nothing and returns no action, ending the loop.
        pass