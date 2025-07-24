import React from 'react';

interface PageLayoutProps {
  children: React.ReactNode;
  background?: string;
  padding?: string;
  title?: string;
  description?: string;
}

const PageLayout: React.FC<PageLayoutProps> = ({
  children,
  background = '#f5f5f5',
  padding = '24px',
  title,
  description
}) => {
  return (
    <div style={{
      minHeight: 'calc(100vh - 64px)',
      background,
      padding
    }}>
      {title && <h1 style={{ marginBottom: '8px' }}>{title}</h1>}
      {description && <p style={{ marginBottom: '24px', color: '#666' }}>{description}</p>}
      {children}
    </div>
  );
};

export default PageLayout;
