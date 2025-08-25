from typing import List, Dict, Any, Optional
import streamlit as st
import time
import logging
from core.text_processor import TextProcessor
from core.llm_client import LLMClient
from utils.heuristics import HeuristicsEngine

logger = logging.getLogger(__name__)

class ClassificationResult:
    """Stores the results of content classification"""
    
    def __init__(self, sentences: List[Dict], stage1_results: List[Dict], 
                 stage2_results: List[Dict] = None, debug_info: Dict = None):
        self.sentences = sentences
        self.stage1_results = stage1_results
        self.stage2_results = stage2_results or []
        self.debug_info = debug_info or {}
        
        # Build lookup maps
        self._stage1_map = {r['hash']: r for r in stage1_results}
        self._stage2_map = {r['hash']: r for r in stage2_results} if stage2_results else {}
    
    def get_sentence_classification(self, sentence_hash: str) -> Dict[str, Any]:
        """Get classification result for a sentence by hash"""
        if sentence_hash in self._stage2_map:
            # Return phrase-level spans
            return {
                'type': 'phrase_level',
                'spans': self._stage2_map[sentence_hash]['spans']
            }
        elif sentence_hash in self._stage1_map:
            # Return sentence-level label
            return {
                'type': 'sentence_level',
                'label': self._stage1_map[sentence_hash]['label']
            }
        else:
            # Fallback
            return {
                'type': 'sentence_level',
                'label': 'info'  # Default fallback
            }
    
    def get_statistics(self) -> Dict[str, int]:
        """Get classification statistics"""
        stats = {'info_count': 0, 'promo_count': 0, 'risk_count': 0}
        
        for sentence in self.sentences:
            classification = self.get_sentence_classification(sentence['hash'])
            
            if classification['type'] == 'phrase_level':
                # Count spans
                for span in classification['spans']:
                    stats[f"{span['label']}_count"] += 1
            else:
                # Count sentence
                stats[f"{classification['label']}_count"] += 1
        
        return stats

class ContentClassifier:
    """Main classifier orchestrating the two-stage classification process"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.text_processor = TextProcessor()
        self.llm_client = LLMClient()
        self.heuristics = HeuristicsEngine()
    
    def classify_content(self, content: str) -> ClassificationResult:
        """
        Main classification method
        Returns ClassificationResult with all analysis data
        """
        debug_info = {} if self.debug_mode else None
        
        try:
            # Step 1: Input processing and normalization
            if self.debug_mode:
                debug_info['raw_input'] = content
            
            normalized_text, normalization_changes = self.text_processor.normalize_text(content)
            if self.debug_mode:
                debug_info['normalized_text'] = normalized_text
                debug_info['normalization_changes'] = normalization_changes
            
            # Step 2: Sentence splitting
            sentences = self.text_processor.split_sentences(normalized_text)
            if self.debug_mode:
                debug_info['sentences'] = sentences
            
            if not sentences:
                return ClassificationResult([], [], [], debug_info)
            
            # Step 3: Stage 1 classification (with batching if needed)
            stage1_results = self._run_stage1_classification(sentences)
            if self.debug_mode:
                debug_info['stage1_results'] = stage1_results
            
            # Step 4: Select candidates for Stage 2
            stage2_candidates = self._select_stage2_candidates(sentences, stage1_results)
            if self.debug_mode:
                debug_info['stage2_candidates'] = stage2_candidates
                debug_info['stage2_criteria'] = self.heuristics.get_last_selection_criteria()
            
            # Step 5: Stage 2 classification (phrase-level)
            stage2_results = []
            if stage2_candidates:
                stage2_results = self._run_stage2_classification(stage2_candidates)
                if self.debug_mode:
                    debug_info['stage2_results'] = stage2_results
            
            return ClassificationResult(
                sentences=sentences,
                stage1_results=stage1_results,
                stage2_results=stage2_results,
                debug_info=debug_info
            )
            
        except Exception as e:
            # In case of error, return minimal result
            if self.debug_mode:
                debug_info['error'] = str(e)
            
            # Try to return what we have so far
            sentences = getattr(self, '_last_sentences', [])
            stage1_results = getattr(self, '_last_stage1_results', [])
            
            return ClassificationResult(sentences, stage1_results, [], debug_info)
    
    def _run_stage1_classification(self, sentences: List[Dict]) -> List[Dict]:
        """Run Stage 1 classification with batching"""
        # Determine if batching is needed
        batch_size = self.llm_client.estimate_batch_size(sentences)
        total_tokens = sum(self.text_processor.estimate_tokens(s['text']) for s in sentences)
        
        if batch_size >= len(sentences):
            # Process all at once
            logger.info(f"Stage 1: Single batch ({len(sentences)} sentences, ~{total_tokens} tokens)")
            results = self.llm_client.classify_sentences_stage1(sentences)
        else:
            # Process in batches
            num_batches = (len(sentences) + batch_size - 1) // batch_size
            logger.info(f"Stage 1: {num_batches} batches ({len(sentences)} sentences, ~{total_tokens} tokens)")
            
            results = []
            for i in range(0, len(sentences), batch_size):
                batch_num = (i // batch_size) + 1
                batch = sentences[i:i + batch_size]
                logger.info(f"Stage 1: Processing batch {batch_num}/{num_batches} ({len(batch)} sentences)")
                
                batch_results = self.llm_client.classify_sentences_stage1(batch)
                logger.info(f"Stage 1: Batch {batch_num} returned {len(batch_results)} results")
                results.extend(batch_results)
                
                # Show progress if in debug mode
                if self.debug_mode:
                    progress = min(100, int((i + batch_size) / len(sentences) * 100))
                    st.write(f"Stage 1 progress: {progress}%")
        
        # Log results summary
        label_counts = {}
        needs_phrase_count = 0
        for result in results:
            label = result['label']
            label_counts[label] = label_counts.get(label, 0) + 1
            if result.get('needs_phrase_level', False):
                needs_phrase_count += 1
        
        logger.info(f"Stage 1 complete: {label_counts.get('info', 0)} info, {label_counts.get('promo', 0)} promo, {label_counts.get('risk', 0)} risk ({needs_phrase_count} flagged for Stage 2)")
        
        self._last_stage1_results = results  # For error recovery
        return results avoid truncation
        if len(sentences) > 20:
            # Force smaller batches for reliability
            batch_size = min(20, len(sentences))
            logger.info(f"Stage 1: Forcing smaller batches due to size ({len(sentences)} sentences)")
        else:
            batch_size = self.llm_client.estimate_batch_size(sentences)
        
        total_tokens = sum(self.text_processor.estimate_tokens(s['text']) for s in sentences)
        
        if batch_size >= len(sentences):
            # Process all at once
            logger.info(f"Stage 1: Single batch ({len(sentences)} sentences, ~{total_tokens} tokens)")
            results = self.llm_client.classify_sentences_stage1(sentences)
        else:
            # Process in batches
            num_batches = (len(sentences) + batch_size - 1) // batch_size
            logger.info(f"Stage 1: {num_batches} batches ({len(sentences)} sentences, ~{total_tokens} tokens)")
            
            results = []
            for i in range(0, len(sentences), batch_size):
                batch_num = (i // batch_size) + 1
                batch = sentences[i:i + batch_size]
                logger.info(f"Stage 1: Processing batch {batch_num}/{num_batches} ({len(batch)} sentences)")
                
                batch_results = self.llm_client.classify_sentences_stage1(batch)
                logger.info(f"Stage 1: Batch {batch_num} returned {len(batch_results)} results")
                results.extend(batch_results)
                
                # Show progress if in debug mode
                if self.debug_mode:
                    progress = min(100, int((i + batch_size) / len(sentences) * 100))
                    st.write(f"Stage 1 progress: {progress}%")
        
        # Log results summary
        label_counts = {}
        needs_phrase_count = 0
        for result in results:
            label = result['label']
            label_counts[label] = label_counts.get(label, 0) + 1
            if result.get('needs_phrase_level', False):
                needs_phrase_count += 1
        
        logger.info(f"Stage 1 complete: {label_counts.get('info', 0)} info, {label_counts.get('promo', 0)} promo, {label_counts.get('risk', 0)} risk ({needs_phrase_count} flagged for Stage 2)")
        
        self._last_stage1_results = results  # For error recovery
        return results
    
    def _select_stage2_candidates(self, sentences: List[Dict], stage1_results: List[Dict]) -> List[Dict]:
        """Select sentences that need phrase-level analysis"""
        candidates = []
        llm_flagged = 0
        heuristic_added = 0
        
        for i, sentence in enumerate(sentences):
            stage1_result = stage1_results[i]
            
            # Primary selection: LLM flagged as needing phrase-level analysis
            if stage1_result.get('needs_phrase_level', False):
                candidates.append(sentence)
                llm_flagged += 1
            # Secondary selection: Heuristic patterns
            elif self.heuristics.should_use_phrase_level(sentence['text']):
                candidates.append(sentence)
                heuristic_added += 1
        
        if candidates:
            criteria = self.heuristics.get_last_selection_criteria()
            logger.info(f"Stage 2: {len(candidates)} candidates selected ({llm_flagged} flagged + {heuristic_added} heuristic)")
            if heuristic_added > 0:
                logger.info(f"Stage 2: Heuristic criteria: {', '.join(criteria) if criteria else 'pattern matching'}")
        else:
            logger.info("Stage 2: No candidates selected")
        
        return candidates
    
    def _run_stage2_classification(self, candidates: List[Dict]) -> List[Dict]:
        """Run Stage 2 classification with validation"""
        if not candidates:
            return []
        
        logger.info(f"Stage 2: Processing {len(candidates)} candidates")
        
        try:
            results = self.llm_client.classify_phrases_stage2(candidates)
            
            # Validate results
            validated_results = []
            validation_failures = 0
            
            for i, result in enumerate(results):
                candidate = candidates[i]
                
                # Validate spans
                if self.text_processor.validate_sentence_bounds(candidate['text'], result['spans']):
                    validated_results.append(result)
                else:
                    # Validation failed, fall back to Stage 1 result
                    validation_failures += 1
                    if self.debug_mode:
                        st.warning(f"Stage 2 validation failed for sentence: {candidate['text'][:50]}...")
                    # Don't add to results - will fall back to Stage 1
            
            logger.info(f"Stage 2 complete: {len(validated_results)} phrase-level results ({validation_failures} validation failures)")
            return validated_results
            
        except Exception as e:
            logger.error(f"Stage 2 failed: {str(e)}")
            if self.debug_mode:
                st.error(f"Stage 2 processing failed: {str(e)}")
            return []