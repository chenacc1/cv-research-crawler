import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

interface MarkdownViewerProps {
  content: string;
}

/** Minimal HAST element type for the rehype plugin */
interface HastElement {
  type: string;
  tagName?: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
}

type HastNode = HastElement | { type: string; value?: string; children?: HastNode[] };

/** Generate a slug from heading text content */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

/** Extract text from HAST children recursively */
function extractText(node: unknown): string {
  if (typeof node === 'string') return node;
  if (!node || typeof node !== 'object') return '';
  const n = node as Record<string, unknown>;
  if (n.type === 'text') return (n.value as string) || '';
  if (Array.isArray(n.children)) {
    return (n.children as unknown[]).map(extractText).join('');
  }
  if (n.children) return extractText(n.children);
  return '';
}

/** Rehype plugin: add id anchors to headings */
function rehypeHeadingAnchors() {
  return (tree: HastElement) => {
    const headingNodes: { node: HastElement; id: string }[] = [];

    function traverse(node: unknown) {
      if (!node || typeof node !== 'object') return;
      const n = node as Record<string, unknown>;
      const children = n.children;
      if (n.type === 'element' && typeof n.tagName === 'string' && /^h[1-6]$/.test(n.tagName as string)) {
        const headingEl = n as unknown as HastElement;
        const text = Array.isArray(children) ? (children as unknown[]).map(extractText).join('') : '';
        const id = slugify(text) || 'heading';
        headingNodes.push({ node: headingEl, id });
      }
      if (Array.isArray(children)) {
        (children as unknown[]).forEach(traverse);
      } else if (typeof children === 'object' && children) {
        traverse(children);
      }
    }

    traverse(tree);

    for (const { node, id } of headingNodes) {
      if (!node.properties) node.properties = {};
      node.properties.id = id;
    }
  };
}

export default function MarkdownViewer({ content }: MarkdownViewerProps) {
  return (
    <div className="prose prose-sm max-w-none prose-headings:mt-6 prose-headings:mb-2 prose-p:my-3 prose-table:border-collapse prose-th:border prose-th:border-gray-300 prose-th:bg-gray-50 prose-th:px-3 prose-th:py-2 prose-td:border prose-td:border-gray-300 prose-td:px-3 prose-td:py-2 prose-code:rounded prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-sm prose-code:before:content-none prose-code:after:content-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeHeadingAnchors]}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
