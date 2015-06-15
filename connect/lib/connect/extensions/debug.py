
def usage():
	yield '@'

def run(*args, **kwargs):
	sys.stdout.write('Configuration:\n')
	import StringIO
	buf = StringIO.StringIO()
	config.write(buf)
	buf = '    ' + buf.getvalue().replace('\n', '\n    ').strip() + '\n'
	sys.stdout.write(buf)
	sys.stdout.write('\n')
	sys.stdout.flush()

	try:
		from IPython.Shell import IPShellEmbed as embed
		if htcondor:
			import classad

		schedd = htcondor.Schedd()
		r = schedd.query()

		params = {}
		for result in r:
			for k in result.keys():
				if k in params:
					params[k] += 1
				else:
					params[k] = 1

		common = []
		for k, v in params.items():
			if v == len(r):
				common.append(k)

		common.sort()

		embed()()

	except Exception, e:
		error('cannot run interactive debugger:\n', e)
