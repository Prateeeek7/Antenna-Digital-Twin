import React from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import './FormulaMarkdown.css';

export interface FormulaMarkdownProps {
  /** GitHub-flavored prose; inline math: `$...$`, display: `$$...$$` (KaTeX). */
  children: string;
  className?: string;
  /** Single paragraph: no extra bottom margin on the wrapper paragraph */
  inlineParagraph?: boolean;
}

const makeComponents = (inlineParagraph: boolean): Partial<Components> => ({
  p: ({ children }) => (
    <p className={inlineParagraph ? 'formula-md-p formula-md-p--tight' : 'formula-md-p'}>{children}</p>
  ),
});

/**
 * Renders Markdown with KaTeX math (remark-math + rehype-katex).
 * Example: `Total length $L \\approx v_f \\lambda/2$ for resonance.`
 */
export const FormulaMarkdown: React.FC<FormulaMarkdownProps> = ({
  children,
  className = '',
  inlineParagraph = false,
}) => {
  const src = children?.trim() ?? '';
  if (!src) return null;

  const mods = [
    'formula-markdown',
    inlineParagraph ? 'formula-markdown--inline-p' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={mods}>
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[[rehypeKatex, { strict: false, throwOnError: false }]]}
        components={makeComponents(inlineParagraph)}
      >
        {src}
      </ReactMarkdown>
    </div>
  );
};
