MOCK_SEARCH_RESULT = {
    "books": [
        {
            "book_id": "7123456789",
            "book_name": "测试小说",
            "author": "测试作者",
            "cover_url": "https://example.com/cover.jpg",
            "word_count": 500000,
            "creation_status": "连载中",
        },
        {
            "book_id": "7987654321",
            "book_name": "另一本测试小说",
            "author": "另一作者",
            "cover_url": "https://example.com/cover2.jpg",
            "word_count": 300000,
            "creation_status": "已完结",
        }
    ],
    "total": 2,
    "page": 0,
}

MOCK_BOOK_DETAIL = {
    "book_id": "7123456789",
    "book_name": "测试小说",
    "author": "测试作者",
    "cover_url": "https://example.com/cover.jpg",
    "word_count": 500000,
    "creation_status": "连载中",
    "last_chapter_title": "第100章 最新章节",
    "last_update_timestamp": 1732752000,
}

MOCK_CHAPTER_LIST = {
    "total_chapters": 5,
    "chapters": [
        {"item_id": "ch_001", "title": "第1章 开始", "chapter_index": 0, "word_count": 3000, "volume_name": "第一卷"},
        {"item_id": "ch_002", "title": "第2章 发展", "chapter_index": 1, "word_count": 3500, "volume_name": "第一卷"},
        {"item_id": "ch_003", "title": "第3章 高潮", "chapter_index": 2, "word_count": 4000, "volume_name": "第一卷"},
        {"item_id": "ch_004", "title": "第4章 转折", "chapter_index": 3, "word_count": 3200, "volume_name": "第二卷"},
        {"item_id": "ch_005", "title": "第5章 结局", "chapter_index": 4, "word_count": 3800, "volume_name": "第二卷"},
    ],
}

MOCK_CHAPTER_CONTENT = {
    "type": "text",
    "content": "这是一段测试的章节内容。\n\n故事开始于一个平凡的早晨，主角醒来发现自己获得了一种神奇的能力...\n\n第二段内容继续描述故事的发展...",
}
