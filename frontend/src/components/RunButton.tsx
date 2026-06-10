import React from 'react';

interface Props {
  onClick: () => void;
  disabled: boolean;
}

function RunButton({ onClick, disabled }: Props) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        px-4 py-1.5 rounded text-sm font-medium transition-all
        ${disabled
          ? 'bg-[#4a4a4a] text-[#888] cursor-not-allowed'
          : 'bg-[#0e639c] hover:bg-[#1177bb] text-white active:bg-[#0d5689]'
        }
      `}
    >
      {disabled ? '▶ Executando...' : '▶ Run'}
    </button>
  );
}

export default RunButton;
