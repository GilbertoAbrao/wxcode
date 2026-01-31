"use client";

import React, { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Play } from "lucide-react";
import { getCommandLabel } from "@/utils/wxcode-commands";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  onSkillClick?: (skill: string) => void;
}

/**
 * Elegant Markdown renderer for chat messages
 * Supports GFM (tables, strikethrough, task lists) and WXCODE skill buttons
 */
function MarkdownRendererComponent({
  content,
  className,
  onSkillClick,
}: MarkdownRendererProps) {
  // Pre-process content to handle /wxcode: commands
  // We'll render them as custom markers that we replace with buttons
  const processedContent = content;

  return (
    <div className={`markdown-content ${className || ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-zinc-100 mt-4 mb-2 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-semibold text-zinc-100 mt-3 mb-2 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold text-zinc-200 mt-3 mb-1 first:mt-0">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-sm font-semibold text-zinc-200 mt-2 mb-1 first:mt-0">
              {children}
            </h4>
          ),

          // Paragraphs
          p: ({ children }) => (
            <p className="text-sm text-zinc-300 leading-relaxed mb-2 last:mb-0">
              {children}
            </p>
          ),

          // Lists
          ul: ({ children }) => (
            <ul className="text-sm text-zinc-300 list-disc list-inside space-y-1 mb-2 ml-2">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="text-sm text-zinc-300 list-decimal list-inside space-y-1 mb-2 ml-2">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-zinc-300">
              {children}
            </li>
          ),

          // Task lists (GFM)
          input: ({ checked }) => (
            <input
              type="checkbox"
              checked={checked}
              readOnly
              className="mr-2 rounded border-zinc-600 bg-zinc-800 text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
            />
          ),

          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-purple-500 pl-3 my-2 text-zinc-400 italic">
              {children}
            </blockquote>
          ),

          // Code blocks
          pre: ({ children }) => (
            <pre className="bg-zinc-900 rounded-lg p-3 my-2 overflow-x-auto text-xs">
              {children}
            </pre>
          ),
          code: ({ children, className }) => {
            const isInline = !className;
            const codeText = String(children).replace(/\n$/, "");

            // Check if it's a /wxcode: command
            if (isInline && codeText.startsWith("/wxcode:")) {
              return (
                <button
                  onClick={() => onSkillClick?.(codeText)}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-purple-700/50 hover:bg-purple-600/50 text-purple-200 rounded text-xs font-medium transition-colors"
                  title={codeText}
                >
                  <Play className="w-2.5 h-2.5" />
                  {getCommandLabel(codeText)}
                </button>
              );
            }

            // Regular inline code
            if (isInline) {
              return (
                <code className="px-1.5 py-0.5 bg-zinc-800 text-purple-300 rounded text-xs font-mono">
                  {children}
                </code>
              );
            }

            // Code block (inside pre)
            return (
              <code className="text-zinc-300 font-mono text-xs">
                {children}
              </code>
            );
          },

          // Tables (GFM)
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full text-xs border-collapse">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-zinc-800/50">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody>
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-zinc-800">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 text-left font-medium text-zinc-300 border-b border-zinc-700">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 text-zinc-400">
              {children}
            </td>
          ),

          // Links
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300 underline underline-offset-2 transition-colors"
            >
              {children}
            </a>
          ),

          // Strong/Bold
          strong: ({ children }) => (
            <strong className="font-semibold text-zinc-100">
              {children}
            </strong>
          ),

          // Emphasis/Italic
          em: ({ children }) => (
            <em className="italic text-zinc-300">
              {children}
            </em>
          ),

          // Strikethrough (GFM)
          del: ({ children }) => (
            <del className="line-through text-zinc-500">
              {children}
            </del>
          ),

          // Horizontal rule
          hr: () => (
            <hr className="my-3 border-zinc-700" />
          ),

          // Images
          img: ({ src, alt }) => (
            <img
              src={src}
              alt={alt}
              className="max-w-full h-auto rounded-lg my-2"
            />
          ),
        }}
      >
        {processedContent}
      </ReactMarkdown>

      {/* Extract and render /wxcode: commands as highlighted buttons at the end */}
      {renderSkillButtons(content, onSkillClick)}
    </div>
  );
}

/**
 * Extract /wxcode: commands and render as buttons at the bottom
 */
function renderSkillButtons(
  content: string,
  onSkillClick?: (skill: string) => void
) {
  const regex = /\/wxcode:[a-z-]+(?:\s+[\w.-]+)?/g;
  const matches = content.match(regex);

  if (!matches || matches.length === 0) return null;

  // Deduplicate
  const unique = [...new Set(matches)];

  return (
    <div className="flex flex-wrap gap-2 pt-3 mt-3 border-t border-zinc-700/50">
      {unique.map((cmd, idx) => (
        <button
          key={idx}
          onClick={() => onSkillClick?.(cmd)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-700/40 hover:bg-purple-600/50 text-purple-200 rounded-lg text-sm font-medium transition-colors border border-purple-600/30"
          title={cmd}
        >
          <Play className="w-3.5 h-3.5" />
          {getCommandLabel(cmd)}
        </button>
      ))}
    </div>
  );
}

export const MarkdownRenderer = memo(MarkdownRendererComponent);
export default MarkdownRenderer;
