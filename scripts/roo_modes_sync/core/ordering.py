#!/usr/bin/env python3
"""
Mode ordering strategies for synchronization.
"""

from typing import Dict, List, Any

try:
    from ..exceptions import ConfigurationError
except ImportError:
    # Fallback for direct execution
    from exceptions import ConfigurationError


class OrderingStrategy:
    """Base class for mode ordering strategies."""
    
    def order_modes(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
        """
        Order modes according to strategy.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            options: Strategy-specific options
            
        Returns:
            List of mode slugs in desired order
        """
        # Get all mode slugs
        all_mode_slugs = self._get_all_mode_slugs(categorized_modes)
        
        # Apply strategy-specific ordering
        ordered_modes = self._apply_strategy(categorized_modes, options)
        
        # Get excluded modes before applying filters
        excluded_modes = set(options.get('exclude', []))
        
        # Apply common filters
        ordered_modes = self._apply_filters(ordered_modes, options)
        
        # Ensure all non-excluded modes are included - add any missing
        missing_modes = [mode for mode in all_mode_slugs if mode not in ordered_modes and mode not in excluded_modes]
        ordered_modes.extend(missing_modes)
        
        return ordered_modes
    
    def _get_all_mode_slugs(self, categorized_modes: Dict[str, List[str]]) -> List[str]:
        """
        Get all mode slugs from categorized_modes.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            
        Returns:
            List of all mode slugs
        """
        all_slugs = []
        for category, slugs in categorized_modes.items():
            all_slugs.extend(slugs)
        return all_slugs
    
    def _apply_strategy(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
        """
        Apply strategy-specific ordering logic.
        This method should be overridden by subclasses.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            options: Strategy-specific options
            
        Returns:
            List of mode slugs in strategy-specific order
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def _apply_filters(self, ordered_modes: List[str], options: Dict[str, Any]) -> List[str]:
        """
        Apply common filters to all strategies.
        
        Args:
            ordered_modes: List of modes in strategy-specific order
            options: Filter options
            
        Returns:
            Filtered and reordered list of mode slugs
        """
        result = ordered_modes.copy()
        
        # Apply exclusion filter
        if 'exclude' in options and options['exclude']:
            excluded_modes = set(options['exclude'])
            result = [mode for mode in result if mode not in excluded_modes]
        
        # Apply priority_first filter
        if 'priority_first' in options and options['priority_first']:
            # Remove priority modes from current result
            priority_modes = [mode for mode in options['priority_first'] if mode in result]
            filtered_result = [mode for mode in result if mode not in priority_modes]
            
            # Add priority modes at the beginning
            result = priority_modes + filtered_result
        
        return result


class StrategicOrderingStrategy(OrderingStrategy):
    """Orders modes based on strategic importance."""
    
    # Define the strategic ordering of core modes
    STRATEGIC_CORE_ORDER = ['code', 'debug', 'ask', 'architect', 'orchestrator', 'docs']
    
    def _apply_strategy(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
        """
        Order modes by strategic importance.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            options: Strategy options
            
        Returns:
            List of mode slugs in strategic order
        """
        result = []
        
        # First, process core modes in strategic order
        core_modes = set(categorized_modes.get('core', []))
        for mode in self.STRATEGIC_CORE_ORDER:
            if mode in core_modes:
                result.append(mode)
        
        # Add any remaining core modes not in the strategic list
        for mode in categorized_modes.get('core', []):
            if mode not in result:
                result.append(mode)
        
        # Next, enhanced modes
        for mode in categorized_modes.get('enhanced', []):
            result.append(mode)
        
        # Next, specialized modes
        for mode in categorized_modes.get('specialized', []):
            result.append(mode)
        
        # Finally, discovered modes
        for mode in categorized_modes.get('discovered', []):
            result.append(mode)
        
        return result


class AlphabeticalOrderingStrategy(OrderingStrategy):
    """Orders modes alphabetically within each category or globally."""
    
    def _apply_strategy(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
        """
        Order modes alphabetically within categories or globally.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            options: Strategy options. If 'global_sort' is True, sorts all modes alphabetically
                    regardless of category. Otherwise sorts within categories.
            
        Returns:
            List of mode slugs in alphabetical order
        """
        # Check if global alphabetical sorting is requested
        if options.get('global_sort', True):  # Default to global sort for simplicity
            # Get all mode slugs and sort them globally
            all_slugs = self._get_all_mode_slugs(categorized_modes)
            return sorted(all_slugs)
        
        # Original behavior: sort within categories
        result = []
        
        # Process each category in order
        categories = ['core', 'enhanced', 'specialized', 'discovered']
        
        for category in categories:
            # Sort slugs within this category alphabetically
            sorted_slugs = sorted(categorized_modes.get(category, []))
            result.extend(sorted_slugs)
        
        return result


class CategoryOrderingStrategy(OrderingStrategy):
    """Orders modes by category with configurable category order."""
    
    DEFAULT_CATEGORY_ORDER = ['core', 'enhanced', 'specialized', 'discovered']
    
    def _apply_strategy(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
        """
        Order modes by category.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            options: Strategy options
            
        Returns:
            List of mode slugs ordered by category
        """
        result = []
        
        # Get category order from options or use default
        category_order = options.get('category_order', self.DEFAULT_CATEGORY_ORDER)
        
        # Check if we should sort within categories
        within_category_order = options.get('within_category_order', 'default')
        
        for category in category_order:
            slugs = categorized_modes.get(category, [])
            
            # Apply within-category ordering
            if within_category_order == 'alphabetical':
                slugs = sorted(slugs)
            
            result.extend(slugs)
        
        return result


class CustomOrderingStrategy(OrderingStrategy):
    """Orders modes based on a custom order provided in options."""
    
    def _apply_strategy(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
        """
        Order modes according to a custom list.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            options: Strategy options, must include 'custom_order'
            
        Returns:
            List of mode slugs in custom order
            
        Raises:
            ConfigurationError: If custom_order is not provided
        """
        if 'custom_order' not in options:
            raise ConfigurationError("CustomOrderingStrategy requires 'custom_order' option")
        
        custom_order = options['custom_order']
        
        # Get all available mode slugs
        all_slugs = self._get_all_mode_slugs(categorized_modes)
        
        # Filter custom order to only include existing modes
        valid_custom_order = [mode for mode in custom_order if mode in all_slugs]
        
        # Add any missing modes not in the custom order
        missing_modes = [mode for mode in all_slugs if mode not in valid_custom_order]
        result = valid_custom_order + missing_modes
        
        return result


class GroupingsOrderingStrategy(OrderingStrategy):
    """Orders modes based on user-defined groups with specific ordering."""
    
    def order_modes(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
        """
        Order modes according to strategy, but only include modes from specified groups.
        
        This overrides the base class behavior to NOT automatically add missing modes,
        since groupings should be selective.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            options: Strategy-specific options
            
        Returns:
            List of mode slugs in desired order from specified groups only
        """
        # Apply strategy-specific ordering
        ordered_modes = self._apply_strategy(categorized_modes, options)
        
        # Apply common filters (exclude, priority_first)
        ordered_modes = self._apply_filters(ordered_modes, options)
        
        # For groupings, we deliberately do NOT add missing modes
        # Only return modes from the specified groups
        
        return ordered_modes
    
    def _apply_strategy(self, categorized_modes: Dict[str, List[str]], options: Dict[str, Any]) -> List[str]:
        """
        Order modes according to user-defined groups.
        
        Args:
            categorized_modes: Dictionary of modes grouped by category
            options: Strategy options, must include 'mode_groups' and either 'active_group' or 'active_groups'
            
        Returns:
            List of mode slugs in groupings order
            
        Raises:
            ConfigurationError: If required options are missing or invalid
        """
        # Validate required options
        if 'mode_groups' not in options:
            raise ConfigurationError("GroupingsOrderingStrategy requires 'mode_groups' option")
        
        mode_groups = options['mode_groups']
        if not isinstance(mode_groups, dict):
            raise ConfigurationError("'mode_groups' must be a dictionary")
        
        # Get all available mode slugs
        all_available_modes = set(self._get_all_mode_slugs(categorized_modes))
        
        # Determine which groups to use
        active_groups = self._get_active_groups(options)
        
        # Validate that all active groups exist
        for group_name in active_groups:
            if group_name not in mode_groups:
                raise ConfigurationError(f"Active group '{group_name}' not found in mode_groups")
        
        # Build the ordered list from active groups
        result = []
        seen_modes = set()
        
        # Process groups in order (if group_order is specified, use it; otherwise use active_groups order)
        group_order = options.get('group_order', active_groups)
        
        for group_name in group_order:
            if group_name in active_groups:  # Only process groups that are active
                group_modes = mode_groups.get(group_name, [])
                
                # Add modes from this group, preserving order and filtering duplicates
                for mode_slug in group_modes:
                    if mode_slug in all_available_modes and mode_slug not in seen_modes:
                        result.append(mode_slug)
                        seen_modes.add(mode_slug)
        
        # Handle priority_modes if specified (should come first regardless of group order)
        if 'priority_modes' in options and options['priority_modes']:
            priority_modes = [mode for mode in options['priority_modes']
                            if mode in all_available_modes and mode in result]
            
            # Remove priority modes from current result
            filtered_result = [mode for mode in result if mode not in priority_modes]
            
            # Add priority modes at the beginning
            result = priority_modes + filtered_result
        
        return result
    
    def _get_active_groups(self, options: Dict[str, Any]) -> List[str]:
        """
        Get the list of active groups from options.
        
        Args:
            options: Strategy options
            
        Returns:
            List of active group names
            
        Raises:
            ConfigurationError: If neither active_group nor active_groups is specified
        """
        if 'active_group' in options:
            # Single active group
            active_group = options['active_group']
            if not isinstance(active_group, str):
                raise ConfigurationError("'active_group' must be a string")
            return [active_group]
        
        elif 'active_groups' in options:
            # Multiple active groups
            active_groups = options['active_groups']
            if not isinstance(active_groups, list):
                raise ConfigurationError("'active_groups' must be a list")
            return active_groups
        
        else:
            raise ConfigurationError("GroupingsOrderingStrategy requires either 'active_group' or 'active_groups' option")


class OrderingStrategyFactory:
    """Factory for creating ordering strategies."""
    
    def create_strategy(self, strategy_name: str) -> OrderingStrategy:
        """
        Create an ordering strategy by name.
        
        Args:
            strategy_name: Name of the strategy to create
            
        Returns:
            An OrderingStrategy instance
            
        Raises:
            ConfigurationError: If strategy name is not recognized
        """
        strategies = {
            'strategic': StrategicOrderingStrategy,
            'alphabetical': AlphabeticalOrderingStrategy,
            'category': CategoryOrderingStrategy,
            'custom': CustomOrderingStrategy,
            'groupings': GroupingsOrderingStrategy
        }
        
        if strategy_name not in strategies:
            raise ConfigurationError(f"Unknown ordering strategy: {strategy_name}")
        
        return strategies[strategy_name]()