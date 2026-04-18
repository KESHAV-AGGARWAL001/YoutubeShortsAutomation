import { useState, useEffect } from 'react';
import { fetchBooks } from '../api/client';
import type { BookInfo } from '../api/types';

interface Props {
  source: 'book' | 'custom';
  onSourceChange: (source: 'book' | 'custom') => void;
  customContent: string;
  onCustomContentChange: (text: string) => void;
  selectedBook: string;
  onBookChange: (filename: string) => void;
}

export function ContentInput({
  source, onSourceChange, customContent, onCustomContentChange,
  selectedBook, onBookChange,
}: Props) {
  const [books, setBooks] = useState<BookInfo[]>([]);

  useEffect(() => {
    fetchBooks().then((data) => {
      setBooks(data.books);
      if (data.current_book && !selectedBook) {
        onBookChange(data.current_book);
      }
    }).catch(() => {});
  }, []);

  return (
    <div className="content-input">
      <div className="source-toggle">
        <label className={source === 'book' ? 'active' : ''}>
          <input
            type="radio"
            name="source"
            value="book"
            checked={source === 'book'}
            onChange={() => onSourceChange('book')}
          />
          From Book
        </label>
        <label className={source === 'custom' ? 'active' : ''}>
          <input
            type="radio"
            name="source"
            value="custom"
            checked={source === 'custom'}
            onChange={() => onSourceChange('custom')}
          />
          Custom Text
        </label>
      </div>

      {source === 'book' ? (
        <div className="book-selector">
          <select
            value={selectedBook}
            onChange={(e) => onBookChange(e.target.value)}
            className="input-field"
          >
            <option value="">Select a book...</option>
            {books.map((b) => (
              <option key={b.filename} value={b.filename}>
                {b.display_name} (page {b.current_page}/{b.total_pages})
              </option>
            ))}
          </select>
        </div>
      ) : (
        <textarea
          className="input-field content-textarea"
          placeholder="Paste your content here..."
          value={customContent}
          onChange={(e) => onCustomContentChange(e.target.value)}
          rows={8}
        />
      )}
    </div>
  );
}
