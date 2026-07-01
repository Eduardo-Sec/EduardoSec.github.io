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
            background: #0a0d0b;
            color: #d4dbd7;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
          }
          .content {
            max-width: 860px;
            margin: 0 auto;
            padding: 48px;
            flex: 1;
          }
          .feed-tag {
            font-family: monospace;
            font-size: 14px;
            color: #10b981;
            margin-bottom: 12px;
          }
          h1 {
            font-size: 44px;
            font-weight: 600;
            color: #ffffff;
            letter-spacing: -0.03em;
            margin-bottom: 8px;
            line-height: 1.08;
          }
          h1 em { color: #10b981; font-style: normal; }
          .feed-desc {
            font-size: 14px;
            color: #8a938e;
            margin-bottom: 16px;
          }
          .subscribe {
            background: #0d1310;
            border: 1px solid #1c2620;
            border-radius: 8px;
            padding: 20px 24px;
            margin: 24px 0 32px;
          }
          .subscribe-title {
            font-family: monospace;
            font-size: 12px;
            color: #10b981;
            margin-bottom: 10px;
            letter-spacing: 0.06em;
          }
          .subscribe p {
            font-size: 13px;
            color: #8a938e;
            margin-bottom: 14px;
            line-height: 1.7;
          }
          .subscribe-url {
            background: #101613;
            border: 1px solid #1c2620;
            border-radius: 6px;
            padding: 10px 14px;
          }
          .subscribe-url code {
            font-family: monospace;
            color: #10b981;
            font-size: 12px;
          }
          .feed-header {
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid #1c2620;
          }
          .items {
            border: 1px solid #1c2620;
            border-radius: 10px;
            overflow: hidden;
          }
          .item {
            padding: 18px 24px;
            background: #0d1310;
            border-bottom: 1px solid #141d18;
            display: flex;
            align-items: center;
            justify-content: space-between;
          }
          .item:last-child { border-bottom: none; }
          .item:hover { background: #101613; }
          .item a {
            font-size: 14px;
            color: #d4dbd7;
            text-decoration: none;
          }
          .item a:hover { color: #10b981; }
          .item-date {
            font-family: monospace;
            font-size: 11px;
            color: #545b57;
          }
          .back {
            display: inline-block;
            font-family: monospace;
            font-size: 12px;
            color: #8a938e;
            text-decoration: none;
            margin-bottom: 20px;
            transition: color 0.15s ease;
          }
          .back:hover { color: #10b981; }
          footer {
            border-top: 1px solid #141d18;
            width: 100%;
          }
          .status-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 48px;
            background: #080b09;
          }
          .status-left {
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #10b981;
            display: inline-block;
          }
          .status-text {
            font-family: monospace;
            font-size: 12px;
            color: #8a938e;
          }
          .status-right {
            font-family: monospace;
            font-size: 12px;
            color: #8a938e;
          }
        </style>
      </head>
      <body>
        <div class="content">
          <div class="feed-header">
            <a href="/" class="back">← ebustamante.dev</a>
            <div class="feed-tag">▸ rss feed</div>
            <h1><xsl:value-of select="/rss/channel/title"/><em>.</em></h1>
            <p class="feed-desc"><xsl:value-of select="/rss/channel/description"/></p>
          </div>
          <div class="subscribe">
            <p class="subscribe-title">what is this?</p>
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
        </div>
        <footer>
          <div class="status-bar">
            <div class="status-left">
              <span class="status-dot"></span>
              <span class="status-text">ebustamante.dev</span>
            </div>
            <div class="status-right">UNO · Omaha, NE</div>
          </div>
        </footer>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
