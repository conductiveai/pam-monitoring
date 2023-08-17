from grpc.aio import UnaryUnaryClientInterceptor, UnaryStreamClientInterceptor, StreamUnaryClientInterceptor, StreamStreamClientInterceptor
from grpc.aio import AioRpcError, UnaryUnaryCall, UnaryStreamCall, StreamUnaryCall, StreamStreamCall

from prometheus_client import Counter, Histogram, Gauge, Summary
import pam_monitoring.utils
class ClientMetricsInterceptor(UnaryUnaryClientInterceptor, UnaryStreamClientInterceptor, StreamUnaryClientInterceptor, StreamStreamClientInterceptor):
    def __init__(self):
        self.request_counter = Counter(
            'grpc_client_requests_total', 'Total client requests', ['grpc_service', 'grpc_method']
        )
        self.request_latency = Histogram(
            'grpc_client_request_latency_seconds', 'Request latency', ['grpc_service', 'grpc_method']
        )
        self.error_counter = Counter(
            'grpc_client_errors_total', 'Total server errors', ['grpc_service', 'grpc_method', 'error_type']
        )
        self.request_size_summary = Summary(
            'grpc_client_request_size_bytes', 'Request size in bytes', ['grpc_service', 'grpc_method']
        )
        self.response_size_summary = Summary(
            'grpc_client_response_size_bytes', 'Response size in bytes', ['grpc_service', 'grpc_method']
        )
        self.in_flight_requests_gauge = Gauge(
            'grpc_client_in_flight_requests', 'In-flight requests', ['grpc_service', 'grpc_method']
        )


    async def intercept_unary_unary(self, continuation, client_call_details, request):
        return await self._intercept(continuation, client_call_details, request)

    async def intercept_unary_stream(self, continuation, client_call_details, request):
        return await self._intercept(continuation, client_call_details, request)

    async def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
        return await self._intercept(continuation, client_call_details, request_iterator)

    async def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
        return await self._intercept(continuation, client_call_details, request_iterator)

    async def _intercept(self, continuation, client_call_details, request_or_iterator):
        method_parts = client_call_details.method.decode('utf-8').split('/')
        service_name, method_name = method_parts[-2], method_parts[-1]

        self.request_counter.labels(service_name, method_name).inc()
        self.in_flight_requests_gauge.labels(service_name, method_name).inc()

        request_size = utils.get_size(request_or_iterator)
        self.request_size_summary.labels(service_name, method_name).observe(request_size)

        call = await continuation(client_call_details, request_or_iterator)
        try:
            with self.request_latency.labels(service_name, method_name).time():
                if isinstance(call, (UnaryUnaryCall, StreamUnaryCall)):
                    response = await call
                    response_size = utils.get_size(response)
                    self.response_size_summary.labels(service_name, method_name).observe(response_size)
                    return response
                elif isinstance(call, (UnaryStreamCall, StreamStreamCall)):
                    async def response_iterator():
                        async for resp in call:
                            response_size = utils.get_size(resp)
                            self.response_size_summary.labels(service_name, method_name).observe(response_size)
                            yield resp
                    return response_iterator()
        except AioRpcError as e:
            self.error_counter.labels(service_name, method_name, str(e.code())).inc()
            raise
        except Exception as e:
            self.error_counter.labels(service_name, method_name, type(e).__name__).inc()
            raise
        finally:
            self.in_flight_requests_gauge.labels(service_name, method_name).dec()
        
