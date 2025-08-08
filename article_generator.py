import time
from models import db, TopicCluster, Article
from utils import safe_print

def _mock_llm_call(prompt):
    """
    A mock function to simulate a call to a Large Language Model.
    In a real application, this would be replaced with a call to an actual LLM API.
    """
    safe_print("--- MOCK LLM CALL ---")
    safe_print(f"PROMPT:\n{prompt}")
    safe_print("--------------------")
    time.sleep(2) # Simulate network latency and processing time

    # Extracting the title from the prompt for a more dynamic mock response
    try:
        title_part = next(line for line in prompt.split('\n') if line.startswith("Title suggestion:"))
        title = title_part.replace("Title suggestion:", "").strip()
    except StopIteration:
        title = "Generated Article"

    meta_description = f"This is a detailed article about {title.lower()}, exploring its key aspects and providing valuable insights. Learn more about its relationship with the main topic."

    body = f"""
# {title}

## Introduction to {title}

This is the beginning of a comprehensive article about **{title}**. This section introduces the fundamental concepts and sets the stage for a deeper exploration. The content here is generated to be substantial, aiming for a high character count as requested. We will delve into various sub-topics, providing detailed explanations, examples, and lists.

### Historical Context
- **Early developments**: Tracing the origins of the topic.
- **Key milestones**: Important events that shaped its current state.
- **Modern relevance**: Why this topic is important today.

## Core Concepts of {title}

Here, we break down the main ideas. This section is designed to be very long and detailed. We will use multiple levels of headings to structure the content effectively.

### Sub-Topic 1: A Deeper Dive
This is a paragraph explaining the first sub-topic. It's filled with placeholder text to increase the character count. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus. Suspendisse lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor. Cras elementum ultrices diam. Maecenas ligula massa, varius a, semper congue, euismod non, mi. Proin porttitor, orci nec nonummy molestie, enim est eleifend mi, non fermentum diam nisl sit amet erat.

#### Sub-Sub-Topic 1.1
1. First item in an ordered list.
2. Second item, providing more detail.
3. Third item, continuing the exploration.

Duis semper. Duis arcu massa, scelerisque vitae, consequat in, pretium a, enim. Pellentesque congue. Ut in risus volutpat libero pharetra tempor. Cras vestibulum bibendum augue. Praesent egestas leo in pede.

## Advanced Applications

This final section discusses advanced applications and future trends related to **{title}**. The purpose is to provide forward-looking insights that are valuable to the reader. The text is intentionally verbose to meet the length requirement.

- **Industry impact**: How it's used in various sectors.
- **Future trends**: What to expect in the coming years.
- **Challenges and opportunities**: A balanced view of the landscape.

This mock article is designed to be over 2000 characters long to simulate a detailed response, though reaching 20,000 characters would require a much larger block of text. This provides a solid foundation for the application's functionality.
"""

    # The response is a single string containing all parts.
    # A real implementation might get a structured JSON response.
    full_response = f"TITLE: {title}\n\nMETA_DESCRIPTION: {meta_description}\n\n---\n\n{body}"
    return full_response


def generate_article_for_cluster(cluster_id):
    """
    Generates an article for a given topic cluster and saves it to the database.
    """
    cluster = db.session.get(TopicCluster, cluster_id)
    if not cluster:
        safe_print(f"Cluster with ID {cluster_id} not found.")
        return

    # Check if an article already exists
    if cluster.articles:
        safe_print(f"Article for cluster '{cluster.name}' already exists. Skipping.")
        return

    pillar_topic = cluster.parent.name if cluster.parent else "a general topic"
    cluster_topic = cluster.name

    # Construct a detailed prompt for the LLM
    prompt = f"""
You are an expert SEO content writer. Your task is to write a comprehensive, high-quality article.

**Main Pillar Topic:** {pillar_topic}
**Specific Cluster Topic for this Article:** {cluster_topic}

**Instructions:**
1.  **Length:** The article must be very detailed, aiming for over 20,000 characters.
2.  **Format:** The output must be in Markdown format.
3.  **Structure:** Use headings (h2, h3, h4), paragraphs, lists (bulleted and numbered), and bold text for emphasis.
4.  **Content:** The article should be well-researched, informative, and engaging. It should deeply explore the **Specific Cluster Topic** while keeping the **Main Pillar Topic** as the overarching theme.
5.  **Output Format:** Start the response with the title and meta description, followed by '---', and then the Markdown body.
    - `TITLE: [Your suggested title here]`
    - `META_DESCRIPTION: [Your suggested meta description here (around 155 characters)]`
    - `---`
    - `[Your full Markdown article body here]`

**Title suggestion:** The Ultimate Guide to {cluster_topic.title()}
"""

    # Simulate the LLM call
    generated_content = _mock_llm_call(prompt)

    # Parse the response
    try:
        header, body_markdown = generated_content.split('\n---\n', 1)
        title = next(line for line in header.split('\n') if line.startswith("TITLE:")).replace("TITLE:", "").strip()
        meta_description = next(line for line in header.split('\n') if line.startswith("META_DESCRIPTION:")).replace("META_DESCRIPTION:", "").strip()
    except (ValueError, StopIteration):
        safe_print("Error parsing LLM response. Saving with placeholder data.")
        title = cluster.name.title()
        meta_description = f"An in-depth look at {cluster.name}."
        body_markdown = generated_content # Save the whole thing if parsing fails

    # Create and save the new article
    new_article = Article(
        title=title,
        meta_description=meta_description,
        tags=f"{pillar_topic}, {cluster_topic}",
        body_markdown=body_markdown,
        topic_cluster_id=cluster.id
    )
    db.session.add(new_article)
    db.session.commit()
    safe_print(f"Successfully generated and saved article for cluster: '{cluster.name}'")
