all:
	chmod +x ./arachnida/setup.sh
	./arachnida/setup.sh

clean:
	rm -rf .venv


.PHONY : all clean 