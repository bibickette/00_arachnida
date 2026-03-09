all:
	chmod +x setup.sh
	./setup.sh

clean:
	rm -rf .venv


.PHONY : all clean 