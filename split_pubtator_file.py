import sys, os
from shutil import rmtree

# python split_pubtator_file.py FPATH NDOCS MAXNS
# Splits a PubTator file into MAXNS splits of NDOCS each
if __name__ == '__main__':
    try:
        fp = sys.argv[1]
        nd = int(sys.argv[2])
        ns = int(sys.argv[3])

        # Create directory for the splits
        SPLIT_DIR = "%s.splits_%s/" % (fp, nd)
        if os.path.exists(SPLIT_DIR):
            shutil.rmtree(SPLIT_DIR)
        else:
            os.makedirs(SPLIT_DIR)
        print "Splitting %s into %s splits of %s docs each, saving splits in %s" % (fp, ns, nd, SPLIT_DIR)
    except:
        print "USAGE: python split_pubtator_file.py FPATH NDOCS_PER_SPLIT MAX_SPLITS"
        sys.exit(1)

    with open(fp, 'rb') as f:
        s     = 0
        d     = 0
        f_out = open(SPLIT_DIR + 'split_%s' % s, 'wb')
        for line in f:
            f_out.write(line)
            if len(line.strip()) == 0:
                d += 1
                if d % nd == 0:
                    f_out.close()
                    s += 1
                    if s < ns:
                        f_out = open(SPLIT_DIR + 'split_%s' % s, 'wb')
                    else:
                        break
        f_out.close()
        print "Split %s." % d
