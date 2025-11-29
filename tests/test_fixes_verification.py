"""
验证修复的三个问题的测试用例

1. WebSocket chapterSummary.segments 错误
2. 完结/连载中状态显示相反
3. 搜索分页支持
"""

import pytest
from pathlib import Path


class TestStatusDisplayFix:
    """测试状态显示修复"""
    
    def test_search_html_status_comparison(self):
        """验证 search.html 使用正确的状态字符串"""
        search_html = Path("app/web/templates/search.html").read_text(encoding="utf-8")
        
        # 应该使用 '已完结' 而非 '完结'
        assert "=== '已完结'" in search_html, "search.html 应使用 '已完结' 进行状态判断"
        assert "=== '完结'" not in search_html.replace("'已完结'", ""), "search.html 不应使用 '完结'"


class TestWebSocketChapterSummaryFix:
    """测试 WebSocket chapterSummary 初始化修复"""
    
    def test_book_detail_chapter_summary_initialization(self):
        """验证 book_detail.html 正确初始化 chapterSummary"""
        book_detail_html = Path("app/web/templates/book_detail.html").read_text(encoding="utf-8")
        
        # 应该初始化为 { segments: [] }
        assert "chapterSummary: { segments: [] }" in book_detail_html, \
            "book_detail.html 应将 chapterSummary 初始化为 { segments: [] }"
        
        # loadChapterSummary 应该处理错误情况
        assert "this.chapterSummary = { segments: [] };" in book_detail_html, \
            "loadChapterSummary() 应在错误时初始化空对象"


class TestSearchPaginationFix:
    """测试搜索分页功能修复"""
    
    def test_search_html_has_pagination_state(self):
        """验证 search.html 有分页相关状态"""
        search_html = Path("app/web/templates/search.html").read_text(encoding="utf-8")
        
        # 检查分页状态字段
        assert "currentPage:" in search_html, "应有 currentPage 字段"
        assert "hasNextPage:" in search_html, "应有 hasNextPage 字段"
        assert "totalResults:" in search_html, "应有 totalResults 字段"
    
    def test_search_html_has_pagination_methods(self):
        """验证 search.html 有分页相关方法"""
        search_html = Path("app/web/templates/search.html").read_text(encoding="utf-8")
        
        # 检查分页方法
        assert "async search(page = 0)" in search_html, "search() 应接受 page 参数"
        assert "checkNextPage" in search_html, "应有 checkNextPage() 方法"
        assert "previousPage()" in search_html, "应有 previousPage() 方法"
        assert "nextPage()" in search_html, "应有 nextPage() 方法"
    
    def test_search_html_includes_page_param_in_api_call(self):
        """验证 search.html 在 API 调用中包含 page 参数"""
        search_html = Path("app/web/templates/search.html").read_text(encoding="utf-8")
        
        # 检查 API 调用包含 page 参数
        assert "&page=${page}" in search_html or "&page=' + page" in search_html, \
            "API 调用应包含 page 参数"
    
    def test_search_html_has_pagination_ui(self):
        """验证 search.html 有分页 UI 控件"""
        search_html = Path("app/web/templates/search.html").read_text(encoding="utf-8")
        
        # 检查分页 UI
        assert "上一页" in search_html, "应有上一页按钮"
        assert "下一页" in search_html, "应有下一页按钮"
        assert "previousPage()" in search_html, "上一页按钮应调用 previousPage()"
        assert "nextPage()" in search_html, "下一页按钮应调用 nextPage()"
    
    def test_search_html_scroll_to_top_on_pagination(self):
        """验证 search.html 在分页时滚动到顶部"""
        search_html = Path("app/web/templates/search.html").read_text(encoding="utf-8")
        
        # 检查滚动逻辑
        assert "window.scrollTo" in search_html, "应调用 window.scrollTo 滚动到顶部"
        assert "behavior: 'smooth'" in search_html, "应使用平滑滚动"


class TestAPICompatibility:
    """测试 API 兼容性"""
    
    def test_fanqie_api_page_param(self):
        """验证番茄 API 页码从 0 开始"""
        from app.api.fanqie import FanqieAPI
        import inspect
        
        # 检查 search 方法签名
        search_sig = inspect.signature(FanqieAPI.search)
        assert "page" in search_sig.parameters, "FanqieAPI.search 应有 page 参数"
        
        # 默认值应为 0
        page_default = search_sig.parameters["page"].default
        assert page_default == 0, f"page 参数默认值应为 0，实际为 {page_default}"
    
    def test_qimao_api_page_param(self):
        """验证七猫 API 页码从 0 开始（内部转换为 page*10）"""
        from app.api.qimao import QimaoAPI
        import inspect
        
        # 检查 search 方法签名
        search_sig = inspect.signature(QimaoAPI.search)
        assert "page" in search_sig.parameters, "QimaoAPI.search 应有 page 参数"
        
        # 默认值应为 0
        page_default = search_sig.parameters["page"].default
        assert page_default == 0, f"page 参数默认值应为 0，实际为 {page_default}"


class TestROADMAPUpdate:
    """测试 ROADMAP 更新"""
    
    def test_roadmap_marks_issues_as_completed(self):
        """验证 ROADMAP.md 将三个问题标记为已完成"""
        roadmap = Path("ROADMAP.md").read_text(encoding="utf-8")
        
        assert "- [x] 修复Websocket进度显示异常的问题" in roadmap, \
            "WebSocket 问题应标记为已完成"
        assert "- [x] 修复完结/连载中状态显示相反的问题" in roadmap, \
            "状态显示问题应标记为已完成"
        assert "- [x] 搜索书籍分页支持" in roadmap, \
            "搜索分页应标记为已完成"


class TestCHANGELOGUpdate:
    """测试 CHANGELOG 更新"""
    
    def test_changelog_documents_fixes(self):
        """验证 CHANGELOG.md 记录了修复"""
        changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
        
        assert "修复 WebSocket 进度显示异常问题" in changelog, \
            "CHANGELOG 应记录 WebSocket 修复"
        assert "修复完结/连载中状态显示相反问题" in changelog, \
            "CHANGELOG 应记录状态显示修复"
        assert "实现搜索书籍分页支持" in changelog, \
            "CHANGELOG 应记录搜索分页功能"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
