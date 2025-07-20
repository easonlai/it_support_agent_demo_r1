import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
import pandas as pd
import os
from typing import List, Dict, Any
import logging
from config.config import Config

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeServer:
    def __init__(self):
        self.knowledge_bases = {}
        self.load_knowledge_bases()
    
    def load_knowledge_bases(self):
        """Load CSV knowledge bases into memory"""
        kb_files = {
            'windows': 'windows_kb.csv',
            'office': 'office_kb.csv', 
            'hardware': 'hardware_kb.csv'
        }
        
        for kb_name, filename in kb_files.items():
            filepath = os.path.join(Config.KNOWLEDGE_BASE_PATH, filename)
            if os.path.exists(filepath):
                try:
                    self.knowledge_bases[kb_name] = pd.read_csv(filepath)
                    logger.info(f"Loaded {kb_name} knowledge base: {len(self.knowledge_bases[kb_name])} entries")
                    
                    # Debug: Print first few entries for office KB
                    if kb_name == 'office':
                        logger.info(f"Office KB sample entries:")
                        for idx, row in self.knowledge_bases[kb_name].head(2).iterrows():
                            logger.info(f"  {row['application']}: {row['issue']}")
                            
                except Exception as e:
                    logger.error(f"Error loading {kb_name} knowledge base: {e}")
            else:
                logger.warning(f"Knowledge base file not found: {filepath}")
                
        logger.info(f"Total knowledge bases loaded: {list(self.knowledge_bases.keys())}")
    
    def search_knowledge(self, kb_name: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant entries with improved matching"""
        if kb_name not in self.knowledge_bases:
            logger.warning(f"Knowledge base '{kb_name}' not found")
            return []
        
        kb = self.knowledge_bases[kb_name]
        query_lower = query.lower().strip()
        
        logger.info(f"Searching {kb_name} KB for query: '{query}'")
        logger.debug(f"Query lowercase: '{query_lower}'")
        
        try:
            results = pd.DataFrame()
            
            # Method 1: Try exact phrase matching first
            logger.debug("Trying exact phrase matching...")
            exact_mask = kb.astype(str).apply(
                lambda x: x.str.lower().str.contains(query_lower, na=False, regex=False)
            ).any(axis=1)
            
            exact_results = kb[exact_mask]
            if len(exact_results) > 0:
                logger.info(f"Exact phrase search found {len(exact_results)} results")
                results = exact_results
            else:
                # Method 2: Smart keyword search
                logger.debug("Exact phrase failed, trying keyword search...")
                
                # Clean and extract meaningful keywords
                stop_words = {'when', 'while', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'against'}
                
                # Split query and filter keywords
                query_tokens = query_lower.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').split()
                keywords = [word.strip() for word in query_tokens if len(word.strip()) > 2 and word.strip() not in stop_words]
                
                logger.debug(f"Extracted keywords: {keywords}")
                
                if keywords:
                    # Score each row based on keyword matches
                    row_scores = []
                    
                    for idx, row in kb.iterrows():
                        score = 0
                        row_text = ' '.join([str(cell).lower() for cell in row.values])
                        
                        for keyword in keywords:
                            if keyword in row_text:
                                # Give higher score for matches in 'issue' column
                                if keyword in str(row.get('issue', '')).lower():
                                    score += 2
                                # Medium score for matches in 'application' column  
                                elif keyword in str(row.get('application', '')).lower():
                                    score += 1.5
                                else:
                                    score += 1
                        
                        row_scores.append((idx, score))
                    
                    # Sort by score and get top matches
                    row_scores.sort(key=lambda x: x[1], reverse=True)
                    logger.debug(f"Row scores: {row_scores}")
                    
                    # Take rows with score > 0
                    matching_indices = [idx for idx, score in row_scores if score > 0]
                    
                    if matching_indices:
                        results = kb.loc[matching_indices[:limit]]
                        logger.info(f"Keyword search found {len(results)} results")
                    else:
                        # Method 3: Fallback - single keyword search
                        logger.debug("Keyword scoring failed, trying single keyword fallback...")
                        
                        for keyword in keywords[:3]:  # Try top 3 keywords
                            fallback_mask = kb.astype(str).apply(
                                lambda x: x.str.lower().str.contains(keyword, na=False, regex=False)
                            ).any(axis=1)
                            
                            fallback_results = kb[fallback_mask]
                            if len(fallback_results) > 0:
                                logger.info(f"Fallback search with '{keyword}' found {len(fallback_results)} results")
                                results = fallback_results
                                break
            
            # Final results
            final_results = results.head(limit)
            logger.info(f"Returning {len(final_results)} results")
            
            # Debug output if no results
            if len(final_results) == 0:
                logger.warning("No results found. Debug info:")
                logger.debug(f"KB size: {len(kb)} entries")
                logger.debug("Sample KB entries:")
                for idx, row in kb.head(3).iterrows():
                    logger.debug(f"  Row {idx}: {dict(row)}")
                    
                # Test if ANY keyword appears in the KB
                logger.debug("Testing individual keywords:")
                query_tokens = query_lower.split()
                for token in query_tokens:
                    if len(token) > 2:
                        test_mask = kb.astype(str).apply(
                            lambda x: x.str.lower().str.contains(token, na=False, regex=False)
                        ).any(axis=1)
                        test_count = sum(test_mask)
                        logger.debug(f"  '{token}': {test_count} matches")
            
            return final_results.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error in search_knowledge: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []

knowledge_server = KnowledgeServer()

@app.route('/search/<kb_name>', methods=['POST'])
def search_knowledge_base(kb_name):
    """API endpoint to search knowledge base"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 5)
        
        results = knowledge_server.search_knowledge(kb_name, query, limit)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        logger.error(f"Error searching {kb_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'knowledge_bases': list(knowledge_server.knowledge_bases.keys()),
        'kb_sizes': {kb: len(df) for kb, df in knowledge_server.knowledge_bases.items()}
    })

@app.route('/debug/<kb_name>', methods=['GET'])
def debug_kb(kb_name):
    """Debug endpoint to inspect knowledge base content"""
    if kb_name not in knowledge_server.knowledge_bases:
        return jsonify({'error': f'Knowledge base {kb_name} not found'}), 404
        
    kb = knowledge_server.knowledge_bases[kb_name]
    return jsonify({
        'kb_name': kb_name,
        'size': len(kb),
        'columns': kb.columns.tolist(),
        'sample_data': kb.head(3).to_dict('records')
    })

@app.route('/test_search/<kb_name>', methods=['POST'])
def test_search(kb_name):
    """Test search endpoint for debugging"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if kb_name not in knowledge_server.knowledge_bases:
            return jsonify({'error': f'Knowledge base {kb_name} not found'}), 404
            
        kb = knowledge_server.knowledge_bases[kb_name]
        query_lower = query.lower()
        
        # Test different search methods
        results = {}
        
        # Method 1: Original
        try:
            mask1 = kb.astype(str).apply(lambda x: x.str.lower().str.contains(query_lower, na=False)).any(axis=1)
            results['method1_original'] = kb[mask1].head(3).to_dict('records')
        except Exception as e:
            results['method1_error'] = str(e)
        
        # Method 2: With regex=False
        try:
            mask2 = kb.astype(str).apply(lambda x: x.str.lower().str.contains(query_lower, na=False, regex=False)).any(axis=1)
            results['method2_regex_false'] = kb[mask2].head(3).to_dict('records')
        except Exception as e:
            results['method2_error'] = str(e)
            
        # Method 3: Column-by-column
        column_results = {}
        for col in kb.columns:
            try:
                col_mask = kb[col].astype(str).str.lower().str.contains(query_lower, na=False, regex=False)
                matches = kb[col_mask]
                if len(matches) > 0:
                    column_results[col] = matches.head(2).to_dict('records')
            except Exception as e:
                column_results[f'{col}_error'] = str(e)
        
        results['column_search'] = column_results
        
        return jsonify({
            'query': query,
            'query_lower': query_lower,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Test search error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.KNOWLEDGE_SERVER_PORT, debug=True)