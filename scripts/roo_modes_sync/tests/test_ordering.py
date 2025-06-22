"""Test cases for mode ordering functionality."""

import pytest
from typing import Dict, List, Any

from roo_modes_sync.core.ordering import (
    OrderingStrategy,
    StrategicOrderingStrategy,
    AlphabeticalOrderingStrategy,
    CategoryOrderingStrategy,
    CustomOrderingStrategy,
    OrderingStrategyFactory
)
from roo_modes_sync.exceptions import ConfigurationError


class TestOrderingStrategy:
    """Test cases for base OrderingStrategy class."""
    
    class TestOrderingStrategyImpl(OrderingStrategy):
        """Concrete implementation for testing base class."""
        
        def _apply_strategy(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
            """Simple implementation that returns all modes in flat list."""
            result = []
            for category, modes in categorized_modes.items():
                result.extend(modes)
            return result
    
    @pytest.fixture
    def strategy(self):
        """Create a base strategy instance for testing."""
        return self.TestOrderingStrategyImpl()
    
    @pytest.fixture
    def sample_modes(self):
        """Create sample categorized modes for testing."""
        return {
            'core': ['code', 'architect', 'debug'],
            'enhanced': ['code-enhanced', 'debug-plus'],
            'specialized': ['security-auditor', 'prompt-enhancer'],
            'discovered': ['custom-mode']
        }
    
    def test_get_all_mode_slugs(self, strategy, sample_modes):
        """Test _get_all_mode_slugs method."""
        all_slugs = strategy._get_all_mode_slugs(sample_modes)
        
        # Check that all mode slugs are included
        assert len(all_slugs) == 8
        for category, slugs in sample_modes.items():
            for slug in slugs:
                assert slug in all_slugs
    
    def test_apply_filters_exclude(self, strategy, sample_modes):
        """Test _apply_filters method with exclude option."""
        # Setup
        ordered_modes = strategy._get_all_mode_slugs(sample_modes)
        options = {'exclude': ['code', 'security-auditor']}
        
        # Test
        filtered_modes = strategy._apply_filters(ordered_modes, options)
        
        # Verify
        assert 'code' not in filtered_modes
        assert 'security-auditor' not in filtered_modes
        assert len(filtered_modes) == len(ordered_modes) - 2
    
    def test_apply_filters_priority_first(self, strategy, sample_modes):
        """Test _apply_filters method with priority_first option."""
        # Setup
        ordered_modes = ['code', 'debug', 'architect', 'code-enhanced', 'custom-mode']
        options = {'priority_first': ['custom-mode', 'architect', 'not-in-list']}
        
        # Test
        filtered_modes = strategy._apply_filters(ordered_modes, options)
        
        # Verify - priority modes should be first in the same order they appear in priority_first
        assert filtered_modes[0] == 'custom-mode'
        assert filtered_modes[1] == 'architect'
        assert 'not-in-list' not in filtered_modes  # Should not add non-existent modes
        assert len(filtered_modes) == len(ordered_modes)  # No modes should be lost
    
    def test_apply_filters_combined(self, strategy, sample_modes):
        """Test _apply_filters method with both exclude and priority_first options."""
        # Setup
        ordered_modes = ['code', 'debug', 'architect', 'code-enhanced', 'custom-mode']
        options = {
            'exclude': ['code-enhanced'],
            'priority_first': ['custom-mode', 'debug']
        }
        
        # Test
        filtered_modes = strategy._apply_filters(ordered_modes, options)
        
        # Verify
        assert filtered_modes[0] == 'custom-mode'
        assert filtered_modes[1] == 'debug'
        assert 'code-enhanced' not in filtered_modes
        assert len(filtered_modes) == len(ordered_modes) - 1
    
    def test_order_modes(self, strategy, sample_modes):
        """Test order_modes method."""
        # Setup
        options = {
            'exclude': ['security-auditor'],
            'priority_first': ['custom-mode', 'debug']
        }
        
        # Test
        ordered_modes = strategy.order_modes(sample_modes, options)
        
        # Verify
        assert ordered_modes[0] == 'custom-mode'
        assert ordered_modes[1] == 'debug'
        assert 'security-auditor' not in ordered_modes
        assert len(ordered_modes) == 7  # 8 total - 1 excluded


class TestStrategicOrderingStrategy:
    """Test cases for StrategicOrderingStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create a strategic ordering strategy for testing."""
        return StrategicOrderingStrategy()
    
    @pytest.fixture
    def sample_modes(self):
        """Create sample categorized modes for testing."""
        return {
            'core': ['code', 'architect', 'debug', 'ask', 'orchestrator'],
            'enhanced': ['code-enhanced', 'debug-plus'],
            'specialized': ['security-auditor'],
            'discovered': ['custom-mode']
        }
    
    def test_apply_strategy(self, strategy, sample_modes):
        """Test _apply_strategy method."""
        # Test
        ordered_modes = strategy._apply_strategy(sample_modes, {})
        
        # Verify strategic order of core modes
        core_positions = {mode: ordered_modes.index(mode) for mode in sample_modes['core']}
        
        # Check that core modes are in strategic order
        assert core_positions['code'] < core_positions['debug']
        assert core_positions['debug'] < core_positions['ask']
        assert core_positions['ask'] < core_positions['architect']
        assert core_positions['architect'] < core_positions['orchestrator']
        
        # Check category ordering
        for enhanced_mode in sample_modes['enhanced']:
            for core_mode in sample_modes['core']:
                assert ordered_modes.index(enhanced_mode) > ordered_modes.index(core_mode)
        
        for specialized_mode in sample_modes['specialized']:
            for enhanced_mode in sample_modes['enhanced']:
                assert ordered_modes.index(specialized_mode) > ordered_modes.index(enhanced_mode)
        
        for discovered_mode in sample_modes['discovered']:
            for specialized_mode in sample_modes['specialized']:
                assert ordered_modes.index(discovered_mode) > ordered_modes.index(specialized_mode)


class TestAlphabeticalOrderingStrategy:
    """Test cases for AlphabeticalOrderingStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create an alphabetical ordering strategy for testing."""
        return AlphabeticalOrderingStrategy()
    
    @pytest.fixture
    def sample_modes(self):
        """Create sample categorized modes for testing."""
        return {
            'core': ['code', 'architect', 'debug'],
            'enhanced': ['debug-plus', 'code-enhanced'],
            'specialized': ['security-auditor', 'prompt-enhancer'],
            'discovered': ['custom-mode', 'another-custom-mode']
        }
    
    def test_apply_strategy(self, strategy, sample_modes):
        """Test _apply_strategy method."""
        # Test with default global_sort=True (global alphabetical sorting)
        ordered_modes = strategy._apply_strategy(sample_modes, {})
        
        # With global_sort=True, all modes should be alphabetically sorted across all categories
        all_mode_slugs = []
        for category, modes in sample_modes.items():
            all_mode_slugs.extend(modes)
        expected_order = sorted(all_mode_slugs)
        
        assert ordered_modes == expected_order
        
        # Test with global_sort=False (category-based alphabetical sorting)
        ordered_modes_category = strategy._apply_strategy(sample_modes, {'global_sort': False})
        
        # Verify category ordering when global_sort is False
        core_end_idx = len(sample_modes['core']) - 1
        enhanced_start_idx = core_end_idx + 1
        enhanced_end_idx = enhanced_start_idx + len(sample_modes['enhanced']) - 1
        specialized_start_idx = enhanced_end_idx + 1
        specialized_end_idx = specialized_start_idx + len(sample_modes['specialized']) - 1
        discovered_start_idx = specialized_end_idx + 1
        
        # Check that core modes come first and are alphabetically sorted
        assert set(ordered_modes_category[0:core_end_idx + 1]) == set(sample_modes['core'])
        assert ordered_modes_category[0:core_end_idx + 1] == sorted(sample_modes['core'])
        
        # Check that enhanced modes come next and are alphabetically sorted
        assert set(ordered_modes_category[enhanced_start_idx:enhanced_end_idx + 1]) == set(sample_modes['enhanced'])
        assert ordered_modes_category[enhanced_start_idx:enhanced_end_idx + 1] == sorted(sample_modes['enhanced'])
        
        # Check that specialized modes come next and are alphabetically sorted
        assert set(ordered_modes_category[specialized_start_idx:specialized_end_idx + 1]) == set(sample_modes['specialized'])
        assert ordered_modes_category[specialized_start_idx:specialized_end_idx + 1] == sorted(sample_modes['specialized'])
        
        # Check that discovered modes come last and are alphabetically sorted
        assert set(ordered_modes_category[discovered_start_idx:]) == set(sample_modes['discovered'])
        assert ordered_modes_category[discovered_start_idx:] == sorted(sample_modes['discovered'])


class TestCategoryOrderingStrategy:
    """Test cases for CategoryOrderingStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create a category ordering strategy for testing."""
        return CategoryOrderingStrategy()
    
    @pytest.fixture
    def sample_modes(self):
        """Create sample categorized modes for testing."""
        return {
            'core': ['code', 'architect', 'debug'],
            'enhanced': ['code-enhanced', 'debug-plus'],
            'specialized': ['security-auditor'],
            'discovered': ['custom-mode']
        }
    
    def test_apply_strategy_default(self, strategy, sample_modes):
        """Test _apply_strategy method with default options."""
        # Test
        ordered_modes = strategy._apply_strategy(sample_modes, {})
        
        # Verify default category order
        core_end_idx = len(sample_modes['core']) - 1
        enhanced_start_idx = core_end_idx + 1
        enhanced_end_idx = enhanced_start_idx + len(sample_modes['enhanced']) - 1
        specialized_start_idx = enhanced_end_idx + 1
        specialized_end_idx = specialized_start_idx + len(sample_modes['specialized']) - 1
        discovered_start_idx = specialized_end_idx + 1
        
        assert set(ordered_modes[0:core_end_idx + 1]) == set(sample_modes['core'])
        assert set(ordered_modes[enhanced_start_idx:enhanced_end_idx + 1]) == set(sample_modes['enhanced'])
        assert set(ordered_modes[specialized_start_idx:specialized_end_idx + 1]) == set(sample_modes['specialized'])
        assert set(ordered_modes[discovered_start_idx:]) == set(sample_modes['discovered'])
    
    def test_apply_strategy_custom_order(self, strategy, sample_modes):
        """Test _apply_strategy method with custom category order."""
        # Setup
        options = {
            'category_order': ['discovered', 'enhanced', 'core', 'specialized']
        }
        
        # Test
        ordered_modes = strategy._apply_strategy(sample_modes, options)
        
        # Verify custom category order
        discovered_end_idx = len(sample_modes['discovered']) - 1
        enhanced_start_idx = discovered_end_idx + 1
        enhanced_end_idx = enhanced_start_idx + len(sample_modes['enhanced']) - 1
        core_start_idx = enhanced_end_idx + 1
        core_end_idx = core_start_idx + len(sample_modes['core']) - 1
        specialized_start_idx = core_end_idx + 1
        
        assert set(ordered_modes[0:discovered_end_idx + 1]) == set(sample_modes['discovered'])
        assert set(ordered_modes[enhanced_start_idx:enhanced_end_idx + 1]) == set(sample_modes['enhanced'])
        assert set(ordered_modes[core_start_idx:core_end_idx + 1]) == set(sample_modes['core'])
        assert set(ordered_modes[specialized_start_idx:]) == set(sample_modes['specialized'])
    
    def test_apply_strategy_alphabetical_within(self, strategy, sample_modes):
        """Test _apply_strategy method with alphabetical within-category ordering."""
        # Setup
        options = {
            'within_category_order': 'alphabetical'
        }
        
        # Test
        ordered_modes = strategy._apply_strategy(sample_modes, options)
        
        # Verify category order with alphabetical sorting within categories
        core_end_idx = len(sample_modes['core']) - 1
        enhanced_start_idx = core_end_idx + 1
        enhanced_end_idx = enhanced_start_idx + len(sample_modes['enhanced']) - 1
        specialized_start_idx = enhanced_end_idx + 1
        specialized_end_idx = specialized_start_idx + len(sample_modes['specialized']) - 1
        discovered_start_idx = specialized_end_idx + 1
        
        assert ordered_modes[0:core_end_idx + 1] == sorted(sample_modes['core'])
        assert ordered_modes[enhanced_start_idx:enhanced_end_idx + 1] == sorted(sample_modes['enhanced'])
        assert ordered_modes[specialized_start_idx:specialized_end_idx + 1] == sorted(sample_modes['specialized'])
        assert ordered_modes[discovered_start_idx:] == sorted(sample_modes['discovered'])


class TestCustomOrderingStrategy:
    """Test cases for CustomOrderingStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Create a custom ordering strategy for testing."""
        return CustomOrderingStrategy()
    
    @pytest.fixture
    def sample_modes(self):
        """Create sample categorized modes for testing."""
        return {
            'core': ['code', 'architect', 'debug'],
            'enhanced': ['code-enhanced', 'debug-plus'],
            'specialized': ['security-auditor'],
            'discovered': ['custom-mode']
        }
    
    def test_apply_strategy_with_custom_order(self, strategy, sample_modes):
        """Test _apply_strategy method with custom order."""
        # Setup
        custom_order = ['debug', 'security-auditor', 'custom-mode', 'code']
        options = {'custom_order': custom_order}
        
        # Test
        ordered_modes = strategy._apply_strategy(sample_modes, options)
        
        # Verify that modes are in the custom order with missing modes appended
        for i, mode in enumerate(custom_order):
            assert ordered_modes[i] == mode
        
        # Verify that all modes are included
        assert set(ordered_modes) == set(strategy._get_all_mode_slugs(sample_modes))
    
    def test_apply_strategy_invalid_modes(self, strategy, sample_modes):
        """Test _apply_strategy method with invalid modes in custom order."""
        # Setup
        custom_order = ['debug', 'not-a-mode', 'custom-mode', 'also-not-a-mode', 'code']
        options = {'custom_order': custom_order}
        
        # Test
        ordered_modes = strategy._apply_strategy(sample_modes, options)
        
        # Verify that only valid modes from custom order are included first
        assert ordered_modes[0] == 'debug'
        assert ordered_modes[1] == 'custom-mode'
        assert ordered_modes[2] == 'code'
        
        # Verify that all modes are included
        assert set(ordered_modes) == set(strategy._get_all_mode_slugs(sample_modes))
        
        # Verify that invalid modes are not included
        assert 'not-a-mode' not in ordered_modes
        assert 'also-not-a-mode' not in ordered_modes
    
    def test_apply_strategy_missing_custom_order(self, strategy, sample_modes):
        """Test _apply_strategy method with missing custom_order option."""
        # Test
        with pytest.raises(ConfigurationError) as exc_info:
            strategy._apply_strategy(sample_modes, {})
        
        # Verify
        assert "CustomOrderingStrategy requires 'custom_order' option" in str(exc_info.value)


class TestOrderingStrategyFactory:
    """Test cases for OrderingStrategyFactory."""
    
    @pytest.fixture
    def factory(self):
        """Create a factory instance for testing."""
        return OrderingStrategyFactory()
    
    def test_create_strategy(self, factory):
        """Test create_strategy method with valid strategy names."""
        # Test all valid strategy types
        strategic = factory.create_strategy('strategic')
        assert isinstance(strategic, StrategicOrderingStrategy)
        
        alphabetical = factory.create_strategy('alphabetical')
        assert isinstance(alphabetical, AlphabeticalOrderingStrategy)
        
        category = factory.create_strategy('category')
        assert isinstance(category, CategoryOrderingStrategy)
        
        custom = factory.create_strategy('custom')
        assert isinstance(custom, CustomOrderingStrategy)
    
    def test_create_strategy_unknown(self, factory):
        """Test create_strategy method with unknown strategy name."""
        # Test
        with pytest.raises(ConfigurationError) as exc_info:
            factory.create_strategy('unknown-strategy')
        
        # Verify
        assert "Unknown ordering strategy: unknown-strategy" in str(exc_info.value)