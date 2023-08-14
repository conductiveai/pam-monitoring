protos:
	cd src/protos; python -m grpc_tools.protoc -I. --python_out=../../src/prometheus-monitoring/ --grpc_python_out=../../src/prometheus-monitoring/ *.proto

server:
	python src/prometheus-monitoring/server.py

client:
	python src/prometheus-monitoring/client.py

simulator:
	python src/prometheus-monitoring/simulator.py
