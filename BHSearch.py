from utilfuncs import Byte4ToInt, Byte2ToInt, IntToByte4, wmemcpyUni, AryByte2ToInt
import re
from tqdm import tqdm
import os
import sqlite3

BH_2TH_KEYSMAX = 1000
BH_BHASHINFO = 49
BH_DATALEN = 53
BH_DATAMAXSIZE = 48
BH_DATASTART = 52
BH_DICTIONTYPE = 45
BH_DIC_SEARCH = 2
BH_ENCODECHAR = 46
BH_EQUAL_SEARCH = 1
BH_HEADEND = 56
BH_HEADERLEN = 44
BH_HEAD_INFO = "(C)PMI (2005-2011) Mobile Search Ver 4.0"
BH_INDEXLEN = 51
BH_INDEXSTART = 50
BH_KEYNUMBER = 47
BH_KEYPOSLEN = 55
BH_KEYPOSSTART = 54
BH_TRIE_SEARCH = 0
INDEX_SUFFIX = "Dic.idx"
SHA_SUFFIX = "Dic.sha"
DB_SUFFIX = ".db"

KCGFont_minus_sign = 45
SH_DIC_SERIAL = 20090923


class BHSearch:

    def __init__(self):
        self.DfrFile = None
        self.PosFile = None
        self.bpPBectorQ = bytearray(16)
        self.bpPBectorR = bytearray(16)
        self.byDfrFileType = 1
        self.byPBectorLen = None
        self.bySW = 0
        self.dwSameKeys = 0
        self.dwpKeyList = [0] * BH_2TH_KEYSMAX
        self.iDataLen = 0
        self.iDataStart = 0
        self.iHeaderLen = 0
        self.iIndexLen = 0
        self.iIndexStart = 0
        self.iKeyNumber = 0
        self.iKeyPoint = 0
        self.iMaxDataSize = 0
        self.m_bSecurityType = True
        self.nw = [2**i for i in range(15)]
        self.cs = [2**i for i in range(8)][::-1]


    def OnDBSecurity(self, lpInput, lpOut, nValue, nLen):

        secubytes = bytearray(5)
        secubytes[0] = 0
        IntToByte4(nValue, secubytes, 1)

        if self.m_bSecurityType:
            i = 0
            while i < nLen:

                lpInput[i] = lpInput[i] ^ secubytes[1]
                i2 = i + 1
                if i2 > nLen:
                    break

                lpInput[i2] = lpInput[i2] ^ secubytes[2]
                i3 = i2 + 1
                if i3 > nLen:
                    break

                lpInput[i3] = lpInput[i3] ^ secubytes[3]
                i4 = i3 + 1
                if i4 > nLen:
                    break

                lpInput[i4] = lpInput[i4] ^ secubytes[4]
                i = i4 + 1
        
        wmemcpyUni(lpInput, nLen, lpOut)
        

    def OpenDB(self, strDBFile1, strDBFile2):

        self.PosFile = open(strDBFile1, 'rb')
        self.DfrFile = open(strDBFile2, 'rb')

        if self.DfrFile is None or self.PosFile is None:
            self.PosFile.close()
            self.DfrFile.close()
            return False
        try:

            smhgstr = bytearray(300)
            Temp = self.DfrFile.read(40)
            if Temp.decode() != BH_HEAD_INFO:
                self.PosFile.close()
                self.DfrFile.close()
                return False

            Temp = self.DfrFile.read(3)
            if Temp[0] != 44:
                self.PosFile.close()
                self.DfrFile.close()
                return False
            
            self.iHeaderLen = Temp[1]
            if self.iHeaderLen > 300:
                self.PosFile.close()
                self.DfrFile.close()
                return False

            Temp = bytearray(self.DfrFile.read(self.iHeaderLen))
            self.OnDBSecurity(Temp, smhgstr, SH_DIC_SERIAL, self.iHeaderLen - 43)
            uc = smhgstr[0]
            iPos2 = 1
            while uc != 56:
                if uc == KCGFont_minus_sign:
                    self.byDfrFileType = smhgstr[iPos2]
                    iPos = iPos2 + 1
                elif uc == 46:
                    self.bySW = smhgstr[iPos2]
                    iPos = iPos2 + 1
                elif uc == 47:
                    self.iKeyNumber = Byte4ToInt(smhgstr, iPos2)
                    iPos = iPos2 + 4
                elif uc == 48:
                    self.iMaxDataSize = Byte4ToInt(smhgstr, iPos2)
                    iPos = iPos2 + 4
                elif uc == 49:
                    self.byPBectorLen = smhgstr[iPos2]
                    iPos3 = iPos2 + 1
                    for i in range(self.byPBectorLen):
                        self.bpPBectorQ[i] = smhgstr[(i * 2) + iPos3]
                        self.bpPBectorR[i] = smhgstr[(i * 2) + iPos3 + 1]
                        iPos = iPos3 + 32
                elif uc == 50:
                    self.iIndexStart = Byte4ToInt(smhgstr, iPos2)
                    iPos = iPos2 + 4
                elif uc == 51:
                    self.iIndexLen = Byte4ToInt(smhgstr, iPos2)
                    iPos = iPos2 + 4
                elif uc == 52:
                    self.iDataStart = Byte4ToInt(smhgstr, iPos2)
                    iPos = iPos2 + 4
                elif uc == 53:
                    self.iDataLen = Byte4ToInt(smhgstr, iPos2)
                    iPos = iPos2 + 4
                else:
                    self.PosFile.close()
                    self.DfrFile.close()
                    return False
                
                uc = smhgstr[iPos]
                iPos2 = iPos + 1
        
            self.iKeyPoint = self.iDataStart
            return True
        
        except IOError as e:
            print(e)

        return


    def CloseDB(self):

        if self.DfrFile is not None:
            try:
                self.DfrFile.close()
            except IOError as e:
                print(e)

        if self.PosFile is not None:
            try:
                self.DfrFile.close()
            except IOError as e:
                print(e)


    def GetKeyData(self):
        """
        retrieves the data with the definition/translation
        for a specific word from the dictionary db
        """

        length = 0
        if self.DfrFile is not None:
            try:
                try:
                    self.DfrFile.seek(self.iKeyPoint)
                except IOError as e:
                    print(e)
                    return -1

                if self.byDfrFileType != 1:
                    temp = ord(self.DfrFile.read(1)) & 0xFF
                    _ = self.DfrFile.read(temp)

                n = ord(self.DfrFile.read(1)) & 0xFF

                _ = self.DfrFile.read(n)

                smhgstr = self.DfrFile.read(4)
                length = Byte4ToInt(smhgstr, 0)

                attribute = self.DfrFile.read(length)

            except IOError as e:
                print(e)
                return -1

        return attribute


    def GetKeyFromIndex(self, nIndex):
        """
        will return the word (in weird unicode format) at index nIndex
        in the Dictionary  db file
        :param nIndex: word index
        :return:
        """
        if nIndex < 0 | nIndex >= self.iKeyNumber:
            return -1
        try:
            self.PosFile.seek(nIndex * 4)
            smhgstr = self.PosFile.read(4)
            self.iKeyPoint = Byte4ToInt(smhgstr, 0)
        except IOError as e:
            print(e)

        return self.GetKeyData()


def MakeDrawData(pbyBuf):
    res = []
    key = []
    m_nBufLen = len(pbyBuf)
    i = 0
    nDataNum = -1
    while i < m_nBufLen:

        if pbyBuf[i] == 33:
            i2 = i + 1
            i = i2 + 1 + (pbyBuf[i2] & 0xFF)
            key = [pbyBuf[i2+1:i]]
        elif pbyBuf[i] == 46:
            i3 = i + 1
            nLen = AryByte2ToInt(pbyBuf, i3)
            i4 = i3 + 2
            i = i4 + nLen
        elif pbyBuf[i] == 35 & nDataNum == -1:
            i = i + 5 + AryByte2ToInt(pbyBuf, i + 3)
        elif pbyBuf[i] == 35:
            nDataLen = AryByte2ToInt(pbyBuf, i + 3)
            i += 5
            if nDataLen > 0:
                res.append(pbyBuf[i:i+nDataLen])
                i += nDataLen
        elif pbyBuf[i] != 13 | nDataNum != -1:
            if pbyBuf[i] != 13:
                if pbyBuf != 34:
                    break
                i += 2
            else:
                i += 1
        elif pbyBuf[i] == 13:
            res.append(bytes([0x0D, 0x00]))
            i += 1
        else:
            i += 1
            nDataNum += 1
    return key, res


def MakeWord(a, b):
    return chr(((b & 0xFF) << 8) | (a & 0xFF))


def convert_array(input_array):
    res = ''
    for element in input_array:
        i = 0
        while i < len(element):
            res += MakeWord(element[i], element[i+1])
            i += 2
    return res


class DicDumper:

    def __init__(self, prefix, dicname=None):
        if len(prefix) != 2:
            raise ValueError("Invalid length")
        if dicname is None:
            self.dicname = prefix + " Dictionary"
        self.prefix = prefix
        self.g_shSearch = BHSearch()
        self.g_shSearch.m_bSecurityType = True
        self.prefixes = list(set([self.prefix, self.prefix[::-1]]))
        self.prefixes.sort(reverse=True)
        self.dbname = ''.join(self.prefixes) + DB_SUFFIX
        if os.path.exists(self.dbname):
            print("> Removing the existing %s database file" % self.dbname)
            os.remove(self.dbname)

        self.conn = sqlite3.connect(self.dbname)

    def _create_db_title(self):
        print("> Creating database")
        self.conn.execute("CREATE TABLE name (dicname text)")
        self.conn.execute("INSERT INTO name VALUES ('%s')" % self.dbname)
        self.conn.commit()

    def _create_db_dict(self, dictionary):
        print("> Inserting data...")
        self.conn.execute("CREATE TABLE dictionary (word text, definition text)")
        self.conn.executemany("INSERT INTO dictionary VALUES (?, ?)", dictionary)
        self.conn.commit()

    def _close_db(self):
        print("> Closing database")
        self.conn.close()

    def dump(self):
        dictionary = []
        # we need to handle monolingual dictionaries like the Korean one (KK)
        for prefix in self.prefixes:
            tqdm.write("> Dumping %s dictionary" % prefix)
            self.g_shSearch.OpenDB(prefix + INDEX_SUFFIX, prefix + SHA_SUFFIX)
            for i in tqdm(range(self.g_shSearch.iKeyNumber)):
                full_data = self.g_shSearch.GetKeyFromIndex(i)
                key, data = MakeDrawData(full_data)
                key = convert_array(key)
                data = convert_array(data)
                # we're not dealing with phonetics right now.
                data = re.sub('\/(.*)\/\r', '', data)
                data = re.sub('\r', '\n', data)
                data = re.sub('ÿ', '', data)
                dictionary.append((key, data))

        self._create_db_title()
        self._create_db_dict(dictionary)

if __name__ == "__main__":
    for lang in ["EK", "KK", "JK", "FK", "RK", "CK", "DK"]:
        print("Dumping %s", lang)
        dd = DicDumper(lang)
        dd.dump()
