<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8"/>
  <xsl:template match="/">
    <html>
      <head>
        <title>RSS Feed</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <style>
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            background: #0f0f0f;
            color: #d0d0d0;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            padding: 48px;
            max-width: 860px;
            margin: 0 auto;
          }
          .feed-tag {
            font-family: monospace;
            font-size: 12px;
            color: #a855f7;
            margin-bottom: 12px;
          }
          h1 {
            font-size: 32px;
            font-weight: 600;
            color: #f4f4f4;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
          }
          h1 em { color: #a855f7; font-style: normal; }
          .feed-desc {
            font-size: 14px;
            color: #888;
            margin-bottom: 16px;
          }
          .subscribe {
            background: #0d0d0d;
            border: 1px solid #1e1e1e;
            border-radius: 8px;
            padding: 16px 20px;
            margin: 24px 0 32px;
            font-size: 13px;
            color: #888;
          }
          .subscribe code {
            font-family: monospace;
            color: #a855f7;
            font-size: 12px;
          }
          .subscribe-title {
          font-family: monospace;
          font-size: 11px;
          color: #a855f7;
          margin-bottom: 8px;
          letter-spacing: 0.06em;
          }
          .subscribe p {
          font-size: 13px;
          color: #888;
          margin-bottom: 12px;
          line-height: 1.7;
          }
          .subscribe-url {
          background: #111;
          border: 1px solid #222;
          border-radius: 6px;
          padding: 10px 14px;
          margin-top: 4px;
          }
          .subscribe-url code {
          font-family: monospace;
          color: #a855f7;
          font-size: 12px;
          }
          .feed-header {
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid #1e1e1e;
          }
          .items {
            border: 1px solid #1e1e1e;
            border-radius: 10px;
            overflow: hidden;
          }
          .item {
            padding: 18px 24px;
            background: #0d0d0d;
            border-bottom: 1px solid #141414;
            display: flex;
            align-items: center;
            justify-content: space-between;
          }
          .item:last-child { border-bottom: none; }
          .item:hover { background: #101010; }
          .item a {
            font-size: 14px;
            color: #d8d8d8;
            text-decoration: none;
          }
          .item a:hover { color: #a855f7; }
          .item-date {
            font-family: monospace;
            font-size: 11px;
            color: #555;
          }
          .back {
          display: inline-block;
          font-family: monospace;
          font-size: 12px;
          color: #555;
          text-decoration: none;
          margin-bottom: 20px;
          transition: color 0.15s ease;
          }
          .back:hover { color: #a855f7; }
          
        </style>
      </head>
      <body>
        <div class="feed-header">
          <a href="/" class="back">← ebustamante.dev</a>
          <div class="feed-tag">// rss feed</div>
          <h1><xsl:value-of select="/rss/channel/title"/><em>.</em></h1>
          <p class="feed-desc"><xsl:value-of select="/rss/channel/description"/></p>
        </div>
        <div class="subscribe">
          <p class="subscribe-title">What is this?</p>
          <p>This is an RSS feed. Subscribe by copying the URL below into any RSS reader like Feedly, NewsBlur, or NetNewsWire and you will get notified when new writeups are published.</p>
          <div class="subscribe-url">
            <code>https://ebustamante.dev/index.xml</code>
          </div>
        </div>
        <div class="items">
          <xsl:for-each select="/rss/channel/item">
            <div class="item">
              <a href="{link}"><xsl:value-of select="title"/></a>
              <span class="item-date"><xsl:value-of select="substring(pubDate, 1, 16)"/></span>
            </div>
          </xsl:for-each>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>