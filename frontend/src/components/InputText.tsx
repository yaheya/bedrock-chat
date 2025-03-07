import React, { HTMLInputTypeAttribute, ReactNode } from 'react';
import { twMerge } from 'tailwind-merge';

type Props = {
  className?: string;
  label?: string;
  type?: HTMLInputTypeAttribute;
  value: string;
  disabled?: boolean;
  placeholder?: string;
  hint?: string;
  errorMessage?: string;
  icon?: ReactNode;
  onChange?: (s: string) => void;
};

const InputText: React.FC<Props> = (props) => {
  return (
    <div className={twMerge('flex flex-col', props.className)}>
      {props.icon && (
        <div className="relative inline-block">
          <div className="absolute left-2 top-2 text-lg">{props.icon}</div>
        </div>
      )}
      <input
        type={props.type ?? 'text'}
        className={twMerge(
          'peer h-9 rounded border p-1',
          props.errorMessage
            ? 'border-2 border-red'
            : 'border-aws-font-color/50',
          props.icon ? 'pl-8' : ''
        )}
        disabled={props.disabled}
        value={props.value}
        placeholder={props.placeholder}
        onChange={(e) => {
          props.onChange ? props.onChange(e.target.value) : null;
        }}
      />

      {props.label && (
        <div
          className={twMerge(
            'order-first text-sm peer-focus:font-semibold peer-focus:italic',
            props.errorMessage
              ? 'font-bold text-red'
              : 'text-dark-gray peer-focus:text-aws-font-color'
          )}>
          {props.label}
        </div>
      )}
      {props.hint && !props.errorMessage && (
        <div className="mt-0.5 text-xs text-gray">{props.hint}</div>
      )}
      {props.errorMessage && (
        <div className="mt-0.5 text-xs text-red">{props.errorMessage}</div>
      )}
    </div>
  );
};

export default InputText;
