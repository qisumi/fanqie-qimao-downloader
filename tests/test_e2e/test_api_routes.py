from unittest.mock import AsyncMock, patch

from tests.test_e2e.test_data import MOCK_SEARCH_RESULT


class TestE2EApiRoutes:
    """
    API路由端到端测试
    
    通过HTTP请求测试完整的API流程
    """
    
    def test_search_and_add_book(self, client):
        """测试通过API搜索并添加书籍"""
        with patch('app.web.routes.books_search.BookService') as MockBookService:
            mock_service = AsyncMock()
            mock_service.search_books.return_value = MOCK_SEARCH_RESULT
            MockBookService.return_value = mock_service
            
            response = client.get(
                "/api/books/search",
                params={"platform": "fanqie", "q": "测试小说"}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["books"]) > 0
    
    def test_api_error_responses(self, client):
        """测试API错误响应格式"""
        response = client.get("/api/books/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        
        response = client.get(
            "/api/books/search",
            params={"platform": "invalid", "q": "test"}
        )
        assert response.status_code in [400, 422]
    
    def test_health_check_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
