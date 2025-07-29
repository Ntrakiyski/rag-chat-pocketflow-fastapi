# filename: app/flows.py

from pocketflow import Flow
from nodes.input_node import InputNode
from nodes.content_processing_node import ContentProcessingNode
from nodes.faq_generation_node import FAQGenerationNode
from nodes.end_node import EndNode

def create_setup_flow() -> Flow:
    """
    Creates and returns the one-time setup and ingestion flow.
    This flow handles initial content processing and embedding.
    """
    input_node = InputNode()
    content_processing_node = ContentProcessingNode()
    end_node = EndNode()

    input_node >> content_processing_node
    content_processing_node - "error" >> end_node
    content_processing_node >> end_node
    
    return Flow(start=input_node)

def create_faq_flow() -> Flow:
    """
    Creates and returns the on-demand FAQ generation flow.
    """
    faq_generation_node = FAQGenerationNode()
    end_node = EndNode()

    faq_generation_node - "error" >> end_node

    return Flow(start=faq_generation_node)