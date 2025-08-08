import nltk
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from models import db, Page, TopicCluster
from app import create_app

def download_nltk_data():
    """Download necessary NLTK data."""
    # This is idempotent, it won't re-download if the data is already present.
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('punkt')

# Call the function to ensure data is available when the module is imported.
download_nltk_data()

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

def preprocess_text(text):
    """
    Preprocesses a single text document:
    1. Tokenize
    2. Lowercase
    3. Remove punctuation
    4. Remove stopwords
    5. Lemmatize
    """
    if text is None:
        return ""
    # Tokenize
    tokens = word_tokenize(text)
    # Lowercase and remove punctuation
    tokens = [word.lower() for word in tokens if word.isalpha()]
    # Remove stopwords
    stop_words = set(stopwords.words('english')) # Assuming English for now
    tokens = [word for word in tokens if word not in stop_words]
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return " ".join(tokens)

def analyze_site_content(site_id):
    """
    Analyzes the content of a site, extracts keywords, and proposes topic clusters.
    """
    app = create_app()
    with app.app_context():
        pages = Page.query.filter_by(site_id=site_id).all()
        if not pages:
            print("No pages found for this site to analyze.")
            return

        documents = [page.content for page in pages]
        processed_docs = [preprocess_text(doc) for doc in documents]

        # Use TF-IDF to find important keywords
        vectorizer = TfidfVectorizer(max_df=0.85, max_features=100)
        tfidf_matrix = vectorizer.fit_transform(processed_docs)
        feature_names = vectorizer.get_feature_names_out()

        # For now, let's just print the top 10 keywords for the whole site
        # In the next step, we'll use this to generate clusters.
        # Sum tf-idf scores for each term across all documents
        sum_tfidf = tfidf_matrix.sum(axis=0)
        tfidf_scores = [(feature_names[i], sum_tfidf[0, i]) for i in range(len(feature_names))]
        sorted_tfidf = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

        print(f"Top 10 keywords for site {site_id}:")
        for term, score in sorted_tfidf[:10]:
            print(f"- {term}: {score:.4f}")

        # Clear existing clusters for this site
        TopicCluster.query.filter_by(site_id=site_id).delete()

        # --- Simple Cluster Generation Logic ---
        # 1. Identify a few pillar topics from the top overall keywords.
        # 2. For each pillar, find other related keywords to be clusters.

        num_pillars = min(3, len(sorted_tfidf))
        pillar_keywords = [term for term, score in sorted_tfidf[:num_pillars]]

        for pillar_keyword in pillar_keywords:
            # Create the pillar topic
            pillar_topic = TopicCluster(name=pillar_keyword, site_id=site_id, parent_id=None)
            db.session.add(pillar_topic)
            db.session.flush() # Flush to get the ID for the parent

            # Find related keywords for clusters
            # A simple way is to find documents where the pillar keyword is strong,
            # and then find other top keywords in those documents.

            # Get indices of documents where the pillar keyword has a non-zero tf-idf score
            pillar_keyword_index = feature_names.tolist().index(pillar_keyword)
            relevant_doc_indices = tfidf_matrix[:, pillar_keyword_index].T.toarray()[0].nonzero()[0]

            cluster_candidates = {}
            # Iterate over the relevant documents
            for doc_index in relevant_doc_indices:
                # Get the tf-idf scores for all terms in this document
                doc_vector = tfidf_matrix[doc_index].toarray().flatten()
                # Get indices of top terms in this doc
                top_term_indices = doc_vector.argsort()[-10:][::-1]

                for term_index in top_term_indices:
                    term = feature_names[term_index]
                    if term != pillar_keyword and term not in pillar_keywords:
                        cluster_candidates[term] = cluster_candidates.get(term, 0) + doc_vector[term_index]

            # Sort cluster candidates by their aggregated tf-idf scores
            sorted_clusters = sorted(cluster_candidates.items(), key=lambda x: x[1], reverse=True)

            # Create cluster topics
            num_clusters = min(5, len(sorted_clusters))
            for cluster_keyword, score in sorted_clusters[:num_clusters]:
                cluster_topic = TopicCluster(name=cluster_keyword, site_id=site_id, parent_id=pillar_topic.id)
                db.session.add(cluster_topic)

        db.session.commit()
        print(f"Generated {num_pillars} topic clusters for site {site_id}.")
