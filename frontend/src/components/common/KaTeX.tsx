import React, { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface KaTeXProps {
  math: string;
  displayMode?: boolean;
  className?: string;
}

export const KaTeX: React.FC<KaTeXProps> = ({ math, displayMode = false, className = '' }) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(math, { displayMode, throwOnError: false });
    } catch {
      return '';
    }
  }, [math, displayMode]);

  const Tag = displayMode ? 'div' : 'span';
  return (
    <Tag
      className={`katex-inline ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
      aria-hidden
    />
  );
};
