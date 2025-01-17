// SearchTextBox.tsx
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { BaseProps } from '../@types/common';
import { PiMagnifyingGlass, PiSpinnerGap, PiX } from 'react-icons/pi';
import { twMerge } from 'tailwind-merge';
import ButtonIcon from './ButtonIcon';
import { useDebouncedCallback } from 'use-debounce';

type Props = BaseProps & {
  value: string;
  placeholder?: string;
  suggestions?: string[];
  isLoading?: boolean;
  disabled?: boolean;
  onChange: (value: string) => void;
  onSearch: (searchText: string) => void;
  onSelect: (value: string) => void;
  onClear?: () => void;
};

const SearchTextBox: React.FC<Props> = (props) => {
  const [isFocused, setIsFocused] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [inputValue, setInputValue] = useState(props.value);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Debounce for search
  const debouncedSearch = useDebouncedCallback((searchText: string) => {
    props.onSearch(searchText);
  }, 300);

  // Reflected the change in input value immediately and executed the debounced search
  const handleInputChange = useCallback(
    (value: string) => {
      setInputValue(value);
      props.onChange(value);
      debouncedSearch(value);
    },
    [props.onChange, debouncedSearch]
  );

  useEffect(() => {
    // Synchronize changes from the outside
    setInputValue(props.value);
  }, [props.value]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!props.suggestions?.length) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < props.suggestions!.length - 1 ? prev + 1 : prev
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        e.preventDefault();
        props.onSelect(props.suggestions[selectedIndex]);
        setIsFocused(false);
      } else if (e.key === 'Escape') {
        setIsFocused(false);
      }
    },
    [props, selectedIndex]
  );

  useEffect(() => {
    if (selectedIndex >= 0) {
      const selectedElement = document.getElementById(
        `suggestion-${selectedIndex}`
      );
      selectedElement?.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  return (
    <div className="relative">
      <div
        className={twMerge(
          'dark:bg-aws-ui-color-dark flex items-center rounded border bg-white',
          props.disabled
            ? 'border-aws-font-color-light/30 dark:border-aws-font-color-dark/30'
            : 'border-aws-font-color-light/50 dark:border-aws-font-color-dark/50'
        )}>
        {props.isLoading ? (
          <PiSpinnerGap className="ml-2 animate-spin text-gray" />
        ) : (
          <PiMagnifyingGlass className="ml-2 text-gray" />
        )}
        <input
          ref={inputRef}
          type="text"
          className={twMerge(
            'dark:text-aws-font-color-dark dark:placeholder-aws-font-color-gray w-full bg-transparent p-2 outline-none',
            props.disabled && 'cursor-not-allowed'
          )}
          value={inputValue}
          placeholder={props.placeholder}
          disabled={props.disabled}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onKeyDown={handleKeyDown}
        />
        {inputValue && props.onClear && (
          <ButtonIcon
            className="mr-1 text-gray"
            disabled={props.disabled}
            onClick={() => {
              props.onClear?.();
              setInputValue('');
              setSelectedIndex(-1);
            }}>
            <PiX />
          </ButtonIcon>
        )}
      </div>

      {isFocused && props.suggestions && props.suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="border-aws-font-color-light/50 dark:border-aws-font-color-dark/50 dark:bg-aws-ui-color-dark absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded border bg-white shadow-lg">
          {props.suggestions.map((suggestion, index) => (
            <div
              id={`suggestion-${index}`}
              key={index}
              className={twMerge(
                'hover:bg-aws-sea-blue-hover-light dark:hover:bg-aws-paper-dark cursor-pointer px-4 py-2',
                selectedIndex === index &&
                  'bg-aws-sea-blue-hover-light dark:bg-aws-paper-dark'
              )}
              onClick={() => {
                props.onSelect(suggestion);
                setIsFocused(false);
              }}>
              {suggestion}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchTextBox;
